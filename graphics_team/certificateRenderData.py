import csv
from ctypes import CDLL
import io
import os
import base64
import base64
import re
import sys
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from graphics_team.models import Certificate_Receivers, Certificate_Template
from insb_port import settings
from django.core.mail import send_mail
from django.conf import settings
import cairosvg

# from ctypes.util import find_library

def load_cairo_dll():
    """Explicitly load Cairo DLL on Windows, do nothing on Linux."""
    if sys.platform.startswith("win"):
        # Folder containing cairo-2.dll and dependencies
        dll_folder = 'CairoSVG Libs'
        if os.path.isdir(dll_folder):
            # Prepend to PATH so all dependencies are found
            os.environ["PATH"] = dll_folder + os.pathsep + os.environ.get("PATH", "")
            # Load cairo-2.dll explicitly
            dll_path = os.path.join(dll_folder, "cairo-2.dll")
            try:
                CDLL(dll_path)
            except OSError as e:
                print(f'Failed to load Cairo DLL: {e}')
        else:
            print(f"Cairo DLL folder not found: {dll_folder}")
                
        # # Use ctypes.util.find_library to locate cairo
        # dll_name = find_library("cairo-2")
        # print("Cairo DLL found by ctypes:", dll_name)

# Call this early, before using CairoSVG
load_cairo_dll()

try:
    import cairosvg
except:
    pass

class Certificate_Manager:

    def extract_data_from_csv(csv_file, certificate_id):
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)
        
        # Optional: skip header
        next(reader, None)

        receivers = []

        for row in reader:
            if len(row) < 2:
                continue  # skip invalid rows

            name, email = row
            receivers.append(
                Certificate_Receivers(
                    certificate_id=certificate_id,
                    name=name.strip(),
                    email=email.strip()
                )
            )
        
        return receivers
    
    def normalize_text_tspans(root, ns):
        """
        Converts multiple <tspan> children inside a <text> element
        into a single <tspan> with combined text.
        """
        for text_elem in root.findall('.//svg:text', ns):
            tspans = text_elem.findall('svg:tspan', ns)

            if len(tspans) > 1:
                # Combine all text content
                combined_text = ''.join([
                    (tspan.text or '') for tspan in tspans
                ])

                # Remove all existing tspans
                for tspan in tspans:
                    text_elem.remove(tspan)

                # Clear direct text
                text_elem.text = None

                # Create one single tspan
                new_tspan = ET.Element('{http://www.w3.org/2000/svg}tspan')
                new_tspan.text = combined_text

                text_elem.append(new_tspan)

    def replace_text_in_element(element, old_text, new_text):
        """
        Recursively searches element text and children to replace old_text with new_text.
        """
        if element.text and old_text in element.text:
            element.text = element.text.replace(old_text, new_text)
        for child in element:
            Certificate_Manager.replace_text_in_element(child, old_text, new_text)
            if child.tail and old_text in child.tail:
                child.tail = child.tail.replace(old_text, new_text)

    def pre_process_svg_certificate(svg_file):

        tree = ET.parse(svg_file)
        root = tree.getroot()
        ns = {'svg': 'http://www.w3.org/2000/svg'}

        Certificate_Manager.normalize_text_tspans(root, ns)
        
        # Regex to parse transform="translate(x y)"
        translate_re = re.compile(r'translate\(\s*([\d.-]+)\s+([\d.-]+)\s*\)')
        # Loop over all <text> elements

        for text_elem in root.findall('.//svg:text', ns):
            transform = text_elem.get('transform')
            if transform:
                match = translate_re.match(transform)
                if match:
                    x, y = match.groups()
                    font_size = int(text_elem.get('font-size', '40').replace('px',''))

                    ################################################################
                    # PUT FONTS IN /.local/fonts/ and also in Private Files/fonts/ #
                    # RUN:  fc-cache -f -v FOR LINUX OR INSTALL FONT IN WINDOWS   ##
                    #                                                              #
                    ################################################################
                    font = ImageFont.truetype(settings.PRIVATE_MEDIA_ROOT + "/fonts/Gistesy.ttf", font_size)
                    text_width = font.getlength('<<NAME>>')
                    original_x = float(x)
                    center_x = original_x + (text_width / 2)

                    # Remove transform and set x/y attributes
                    text_elem.attrib.pop('transform')
                    text_elem.set('x', str(center_x))
                    text_elem.set('y', y)
                    # Add centering attributes
                    text_elem.set('text-anchor', 'middle')
            
                    # Handle <tspan> children
                    for tspan in text_elem.findall('.//svg:tspan', ns):
                        # Remove x and y attributes so they inherit from parent <text>
                        if 'x' in tspan.attrib:
                            tspan.attrib.pop('x')
                        if 'y' in tspan.attrib:
                            tspan.attrib.pop('y')
        
        # Serialize modified SVG to bytes
        svg_bytes = io.BytesIO()
        tree.write(svg_bytes, encoding='utf-8', xml_declaration=True)
        svg_bytes.seek(0)  # rewind to the beginning

        content_file = ContentFile(svg_bytes.read(), name=svg_file.name)
        svg_bytes.close()

        return content_file

    def generate_certificate(svg_file, receiver_name):

        svg_file.open('rb')
        svg_content = svg_file.read().decode('utf-8')
        svg_file.close()

        tree = ET.ElementTree(ET.fromstring(svg_content))
        root = tree.getroot()
        ns = {'svg': 'http://www.w3.org/2000/svg'}

        # The text to search for
        old_text = '<<NAME>>'

        # Loop over all <text> elements
        for text_elem in root.findall('.//svg:text', ns):                            
            Certificate_Manager.replace_text_in_element(text_elem, old_text, receiver_name)

        updated_svg = ET.tostring(root, encoding='unicode')

        try:
            png_bytes = cairosvg.svg2png(
                bytestring=updated_svg.encode('utf-8'),
                background_color='white'  # remove transparency
            )

            return png_bytes
        except Exception as e:
            print("Cairo SVG Error:", repr(e))
            return None

    @staticmethod
    def replace_name_with_font_image(root, ns, receiver_name):
        font_path = settings.PRIVATE_MEDIA_ROOT + "/fonts/Gistesy.ttf"

        for text_elem in root.findall('.//svg:text', ns):
            element_text = ''.join(text_elem.itertext())

            if '<<NAME>>' not in element_text:
                continue

            font_size_value = text_elem.get('font-size', '40').replace('px', '')
            try:
                font_size = int(float(font_size_value))
            except:
                font_size = 40

            font = ImageFont.truetype(font_path, font_size)

            bbox = font.getbbox(receiver_name)
            text_width = max(1, bbox[2] - bbox[0])
            text_height = max(1, bbox[3] - bbox[1])

            padding = max(10, int(font_size * 0.25))
            image_width = text_width + (padding * 2)
            image_height = text_height + (padding * 2)

            image = Image.new("RGBA", (image_width, image_height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(image)

            fill = text_elem.get('fill', '#000000')

            draw.text(
                (padding - bbox[0], padding - bbox[1]),
                receiver_name,
                font=font,
                fill=fill
            )

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
            buffer.close()

            x_value = text_elem.get('x', '0')
            y_value = text_elem.get('y', '0')

            try:
                x = float(x_value)
            except:
                x = 0.0

            try:
                y = float(y_value)
            except:
                y = 0.0

            text_anchor = text_elem.get('text-anchor', 'start')

            if text_anchor == 'middle':
                image_x = x - (image_width / 2)
            elif text_anchor == 'end':
                image_x = x - image_width
            else:
                image_x = x

            image_y = y - image_height + padding

            image_elem = ET.Element('{http://www.w3.org/2000/svg}image')
            image_elem.set('x', str(image_x))
            image_elem.set('y', str(image_y))
            image_elem.set('width', str(image_width))
            image_elem.set('height', str(image_height))
            image_elem.set('{http://www.w3.org/1999/xlink}href', f'data:image/png;base64,{encoded_image}')

            parent = None
            for possible_parent in root.iter():
                if text_elem in list(possible_parent):
                    parent = possible_parent
                    break

            if parent is not None:
                index = list(parent).index(text_elem)
                parent.remove(text_elem)
                parent.insert(index, image_elem)

            break

    def generate_certificate_pdf(svg_file, receiver_name):

        svg_file.open('rb')
        svg_content = svg_file.read().decode('utf-8')
        svg_file.close()

        tree = ET.ElementTree(ET.fromstring(svg_content))
        root = tree.getroot()

        ns = {
            'svg': 'http://www.w3.org/2000/svg'
        }

        old_text = '<<NAME>>'

        Certificate_Manager.replace_name_with_font_image(
            root,
            ns,
            receiver_name
        )

        for text_elem in root.findall('.//svg:text', ns):
            Certificate_Manager.replace_text_in_element(
                text_elem,
                old_text,
                receiver_name
            )

        updated_svg = ET.tostring(
            root,
            encoding='unicode'
        )

        try:
            pdf_bytes = cairosvg.svg2pdf(
                bytestring=updated_svg.encode('utf-8')
            )

            return pdf_bytes

        except Exception as e:
            print("Cairo PDF Error:", repr(e))
            return None
        
    def delete_certificate_template_file(certificate_template_obj:Certificate_Template):

        try:
            path = settings.PRIVATE_MEDIA_ROOT+str(certificate_template_obj.svg_template)
            if os.path.exists(path):
                os.remove(path)
            return True
        except:
            return False


    @staticmethod
    def embed_gistesy_font(svg_content):
        font_path = os.path.join(
            settings.PRIVATE_MEDIA_ROOT,
            "fonts",
            "Gistesy.ttf"
        )

        if not os.path.exists(font_path):
            print("Gistesy font not found:", font_path)
            return svg_content

        with open(font_path, "rb") as font_file:
            font_base64 = base64.b64encode(
                font_file.read()
            ).decode("utf-8")

        font_style = f"""
        <style type="text/css">
            @font-face {{
                font-family: 'Gistesy';
                src: url('data:font/ttf;base64,{font_base64}') format('truetype');
            }}

            #recipient-name {{
                font-family: 'Gistesy' !important;
            }}
        </style>
        """

        svg_content = svg_content.replace(
            ">",
            ">" + font_style,
            1
        )

        return svg_content

        
    def sendOTPToUserViaEmail(request, user_email, otp):
        
        '''Sends an email to the users email (The personal email they provided when they registered for the event) with the OTP to get their certificate'''
                
        subject="Your OTP for Certificate - IEEE NSU SB Portal"
                
        message=f"Dear user,\nYour OTP for certificate is:\n{otp}\n\nPlease, do not share this link anywhere else.\nThank you.\n\nThis message was generated from IEEE NSU SB Portal System. If you are not supposed to recieve this email, please contact our Website Development Team."
        
        email_from = settings.EMAIL_HOST_USER
        
        recipient_list = [user_email]
        try:
            send_mail(
                    subject, message, email_from, recipient_list
                )
            mail_sent=True
        except Exception as e:
            mail_sent=False
            print(e)
        
        return mail_sent #the function returns if the mail is sent or not.