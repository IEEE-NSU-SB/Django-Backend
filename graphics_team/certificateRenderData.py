
import csv
from ctypes import CDLL
import io
import os
import re
import sys
import xml.etree.ElementTree as ET
from PIL import ImageFont
from django.core.files.base import ContentFile
from graphics_team.models import Certificate_Receivers
from insb_port import settings
from django.core.mail import send_mail

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
                    font = ImageFont.truetype("C:/Users/Hp/Downloads/Gistesy.ttf", font_size)
                    text_width = font.getlength('Mirza Farhan Shahriar')
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
        old_text = 'Mirza Farhan Shahriar'

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
        except:
            print('Cairo SVG Error')
            return None
        
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