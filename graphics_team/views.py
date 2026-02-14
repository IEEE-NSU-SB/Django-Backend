import csv
import io
import os
import re
# import cairosvg
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from graphics_team.manage_access import GraphicsTeam_Render_Access
from system_administration.render_access import Access_Render
from users.models import Members
from central_branch.renderData import Branch
from port.models import Roles_and_Position
from django.contrib import messages
from system_administration.models import Graphics_Data_Access
from .renderData import GraphicsTeam
from users.renderData import LoggedinUser
from . import renderData
from django.conf import settings
from central_events.models import Events
from .models import Certificate, Certificate_Receivers, Certificate_Template, Graphics_Banner_Image,Graphics_Link,Graphics_Drive_links
import traceback
import logging
from system_administration.system_error_handling import ErrorHandling
from django.http import Http404, HttpResponse,HttpResponseBadRequest
from datetime import datetime
from port.renderData import PortData
from users.renderData import PanelMembersData,member_login_permission
from users import renderData
from central_branch import views as cv
from django.db.models import Count
import xml.etree.ElementTree as ET

logger=logging.getLogger(__name__)
# Create your views here.
@login_required
@member_login_permission
def team_homepage(request):

    try:

        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        
        get_team_members=GraphicsTeam.get_team_members_with_positions()
        context={
            'all_sc_ag':sc_ag,
            'co_ordinators':get_team_members[0],
            'incharges':get_team_members[1],
            'media_url':settings.MEDIA_URL,
            'user_data':user_data,
            'core_volunteers':get_team_members[2],
            'team_volunteers':get_team_members[3],
        }


        return render(request,"Homepage/graphics_homepage.html",context)
    
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)

@login_required
@member_login_permission
def manage_team(request):

    try:

        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        '''This function loads the manage team page for graphics team and is accessable
        by the co-ordinatiors and other admin users only, unless the co-ordinators gives access to others as well'''
        
        sc_ag=PortData.get_all_sc_ag(request=request)
        has_access = GraphicsTeam_Render_Access.access_for_manage_team(request)
        if has_access:
            data_access = GraphicsTeam.load_data_access()
            team_members = GraphicsTeam.load_team_members()
            #load all position for insb members
            position=PortData.get_all_volunteer_position_with_sc_ag_id(request=request,sc_ag_primary=1)
                    
            #load all insb members
            all_insb_members=Members.objects.all()
            #load all current panel members
            current_panel_members = Branch.load_current_panel_members()

            if request.method == "POST":
                if (request.POST.get('add_member_to_team')):
                    #get selected members
                    members_to_add=request.POST.getlist('member_select1')
                    #get position
                    position=request.POST.get('position')
                    for member in members_to_add:
                        GraphicsTeam.add_member_to_team(member,position)
                    messages.success(request,"Added new Members to the Team!")
                    return redirect('graphics_team:manage_team')
                
                if (request.POST.get('remove_member')):
                    '''To remove member from team table'''
                    try:
                        load_current_panel=Branch.load_current_panel()
                        PanelMembersData.remove_member_from_panel(ieee_id=request.POST['remove_ieee_id'],panel_id=load_current_panel.pk,request=request)
                        try:
                            Graphics_Data_Access.objects.filter(ieee_id=request.POST['remove_ieee_id']).delete()
                        except Graphics_Data_Access.DoesNotExist:
                            return redirect('graphics_team:manage_team')
                        return redirect('graphics_team:manage_team')
                    except:
                        pass

                if request.POST.get('access_update'):
                    manage_team_access = False
                    if(request.POST.get('manage_team_access')):
                        manage_team_access=True
                    event_access=False
                    if(request.POST.get('event_access')):
                        event_access=True
                    graphics_access=False
                    if(request.POST.get('graphics_access')):
                        graphics_access=True
                    graphics_view_access=False
                    if(request.POST.get('graphics_view_access')):
                        graphics_view_access=True
                    ieee_id=request.POST['access_ieee_id']
                    if (GraphicsTeam.graphics_manage_team_access_modifications(manage_team_access, event_access, graphics_access, graphics_view_access, ieee_id)):
                        permission_updated_for=Members.objects.get(ieee_id=ieee_id)
                        messages.info(request,f"Permission Details Was Updated for {permission_updated_for.name}")
                    else:
                        messages.info(request,f"Something Went Wrong! Please Contact System Administrator about this issue")

                if request.POST.get('access_remove'):
                    '''To remove record from data access table'''
                    
                    ieeeId=request.POST['access_ieee_id']
                    if(GraphicsTeam.remove_member_from_manage_team_access(ieee_id=ieeeId)):
                        messages.info(request,"Removed member from Managing Team")
                        return redirect('graphics_team:manage_team')
                    else:
                        messages.info(request,"Something went wrong!")

                if request.POST.get('update_data_access_member'):
                    
                    new_data_access_member_list=request.POST.getlist('member_select')
                    
                    if(len(new_data_access_member_list)>0):
                        for ieeeID in new_data_access_member_list:
                            if(GraphicsTeam.add_member_to_manage_team_access(ieeeID)=="exists"):
                                messages.info(request,f"The member with IEEE Id: {ieeeID} already exists in the Data Access Table")
                            elif(GraphicsTeam.add_member_to_manage_team_access(ieeeID)==False):
                                messages.info(request,"Something Went wrong! Please try again")
                            elif(GraphicsTeam.add_member_to_manage_team_access(ieeeID)==True):
                                messages.info(request,f"Member with {ieeeID} was added to the team table!")
                                return redirect('graphics_team:manage_team')

            context={
                'data_access':data_access,
                'members':team_members,
                'insb_members':all_insb_members,
                'current_panel_members':current_panel_members,
                'positions':position,
                'all_sc_ag':sc_ag,
                'user_data':user_data,
            }  
            return render(request,"graphics_team/manage_team.html",context=context)
        else:
            return render(request,"access_denied2.html", { 'all_sc_ag' : sc_ag ,'user_data':user_data,})
        
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)

@login_required
@member_login_permission
def event_page(request):

    try:

        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        '''Only events organised by INSB would be shown on the event page of Graphics Team
        So, only those events are being retrieved from database'''
        insb_organised_events = Branch.load_insb_organised_events()
        sc_ag=PortData.get_all_sc_ag(request=request)
    
        context = {
            'all_sc_ag':sc_ag,
            'events_of_insb_only':insb_organised_events,
            'user_data':user_data,
        }


        return render(request,"Events/graphics_team_events.html",context)
    
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)
@login_required
@member_login_permission
def event_form(request,event_id):

    sc_ag=PortData.get_all_sc_ag(request=request)
    current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
    user_data=current_user.getUserData() #getting user data as dictionary file
    #Initially loading the events whose  links and images were previously uploaded
    #and can be editible

    try:
        sc_ag=PortData.get_all_sc_ag(request=request)
        has_access = GraphicsTeam_Render_Access.access_for_events(request)
        if(has_access):
            #Getting media links and images from database. If does not exist then they are set to none
            try:
                graphics_link = Graphics_Link.objects.get(event_id = Events.objects.get(pk=event_id))
            except:
                graphics_link = None
            try:
                graphic_banner_image = Graphics_Banner_Image.objects.get(event_id = Events.objects.get(pk=event_id))
                image_number = 1
            except:
                graphic_banner_image = None
                image_number = 0

            
            if request.method == "POST":

                if request.POST.get('save'):

                    #getting all data from page
                    drive_link_folder = request.POST.get('drive_link_of_graphics')
                    selected_images = request.FILES.get('image')
                    if(GraphicsTeam.add_links_and_images(drive_link_folder,selected_images,event_id)):
                        messages.success(request,'Saved Changes!')
                    else:
                        messages.error(request,'Please Fill All Fields Properly!')
                    return redirect("graphics_team:event_form",event_id)
                
                if request.POST.get('remove_image'):

                    #When a particular picture is deleted, it gets the image url from the modal

                    image_url = request.POST.get('remove_image')
                    if(GraphicsTeam.remove_image(image_url,event_id)):
                        messages.success(request,'Saved Changes!')
                    else:
                        messages.error(request,'Something went wrong')
                    return redirect("graphics_team:event_form",event_id)

            context={
                'is_branch':True,
                'user_data':user_data,
                'all_sc_ag':sc_ag,
                'graphic_links' : graphics_link,
                'graphics_banner_image':graphic_banner_image,
                'media_url':settings.MEDIA_URL,
                'allowed_image_upload':1-image_number,
                'event_id' : event_id
            }
            return render(request,"Events/graphics_event_form.html",context)
        else:
            return redirect('main_website:event_details', event_id)
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)
    

@login_required
@member_login_permission
def event_form_add_links(request,event_id):
    sc_ag=PortData.get_all_sc_ag(request=request)
    current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
    user_data=current_user.getUserData() #getting user data as dictionary file
    try:
        sc_ag=PortData.get_all_sc_ag(request=request)
        all_graphics_link = GraphicsTeam.get_all_graphics_form_link(event_id)
        has_access = GraphicsTeam_Render_Access.access_for_events(request)

        if (has_access):
            if(request.method == "POST"):
                
                if request.POST.get('add_link'):

                    form_link = request.POST.get('graphics_form_link')
                    title =request.POST.get('title')
                    if GraphicsTeam.add_graphics_form_link(event_id,form_link,title):
                        messages.success(request,'Saved Changes!')
                    else:
                        messages.error(request,'Something went wrong')
                    return redirect("graphics_team:add_link_event_form",event_id)
                
                if request.POST.get('update_link'):

                    form_link = request.POST.get('form_link')
                    title =request.POST.get('title')
                    pk = request.POST.get('link_pk')
                    if GraphicsTeam.update_graphics_form_link(form_link,title,pk):
                        messages.success(request,'Updated Successfully!')
                    else:
                        messages.error(request,'Something went wrong')
                    return redirect("graphics_team:add_link_event_form",event_id)
                
                if request.POST.get('remove_form_link'):

                    id = request.POST.get('remove_link')
                    if GraphicsTeam.remove_graphics_form_link(id):
                        messages.success(request,'Deleted Successfully!')
                    else:
                        messages.error(request,'Something went wrong')
                    return redirect("graphics_team:add_link_event_form",event_id)
                  
            context = {
                'user_data':user_data,
                'all_sc_ag':sc_ag,
                'event_id':event_id,
                'all_graphics_link':all_graphics_link,
            }

            return render(request,"Events/graphics_team_event_form_add_links.html", context)
        else:
            return redirect('main_website:event_details', event_id)
        
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)

@login_required
@member_login_permission
def graphics_drive_links(request):

    try:
        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        
        has_graphics_access = GraphicsTeam_Render_Access.access_for_graphics(request)
        has_access = has_graphics_access or GraphicsTeam_Render_Access.access_for_view_graphics(request)
        if has_access:
            all_links = Graphics_Drive_links.objects.all()
            if request.method == "POST" and has_graphics_access:

                if request.POST.get('add_link'):
                    
                    link_title = request.POST.get('title')
                    link = request.POST.get('graphics_form_link')

                    if GraphicsTeam.add_graphics_drive_links(link_title,link):
                        messages.success(request,'Added Successfully')
                    else:
                        messages.error(request,'Something went wrong')
                    return redirect('graphics_team:graphics_drive_links')
                
                if request.POST.get('update_link'):

                    edit_title = request.POST.get('edit_title')
                    edit_link = request.POST.get('edit_drive_link')
                    link_pk = request.POST.get('link_pk')

                    if GraphicsTeam.edit_graphics_drive_links(edit_title,edit_link,link_pk):
                        messages.success(request,'Updated Successfully')
                    else:
                        messages.error(request,'Something went wrong')
                    return redirect('graphics_team:graphics_drive_links')
                
                if request.POST.get('delete_link'):

                    link_pk = request.POST.get('remove_link')
                    
                    if GraphicsTeam.remove_graphics_drive_link(link_pk):
                        messages.success(request,'Deleted Successfully')
                    else:
                        messages.error(request,'Something went wrong')
                    return redirect('graphics_team:graphics_drive_links')


            context = {
                'user_data':user_data,
                'all_sc_ag':sc_ag,
                'all_links':all_links,
                'has_graphics_access':has_graphics_access
            }
            
            return render(request,"Graphics/graphics_page.html",context)
        else:
            return render(request,"access_denied2.html", { 'all_sc_ag' : sc_ag ,'user_data':user_data,})   
        
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)
    

@login_required
@member_login_permission
def certificates_homepage(request):
    
    try:
        if request.method == 'POST':
            event_id = request.POST.get('event_id')

            return redirect('graphics_team:event_certificates', event_id)
        
        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file

        all_events = Events.objects.all().values('id', 'event_name').order_by('-start_date','-event_date')[:20]
        events_with_certificates = (
            Events.objects
            .annotate(cert_count=Count('certificate_types'))
            .filter(cert_count__gt=0)
            .values('id', 'event_name')
        )

        context = {
            'user_data':user_data,
            'all_sc_ag':sc_ag,
            'all_events':all_events,
            'events_with_certificates':events_with_certificates,
        }

        return render(request, "certificate/certificate_page.html", context)
    
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)

from PIL import ImageFont
@login_required
@member_login_permission
def event_certificates(request, event_id):

    try:
        if request.method == 'POST':
            if 'create_certificate' in request.POST:
                certificate_title = request.POST.get('certificate_name')

                certificate = Certificate.objects.create(event_id=event_id, title=certificate_title)
                
                if request.FILES.get('svg_template'):
                    svg_template = request.FILES.get('svg_template')
                    tree = ET.parse(svg_template)
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

                    # Save to model using Django File
                    from django.core.files.base import ContentFile
                    Certificate_Template.objects.create(
                        certificate_id=certificate.id,
                        svg_template=ContentFile(svg_bytes.read(), name=svg_template.name)
                    )

                if request.FILES.get('csv_file'):
                    csv_file = request.FILES.get('csv_file')

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
                                certificate_id=certificate.id,
                                name=name.strip(),
                                email=email.strip()
                            )
                        )

                    Certificate_Receivers.objects.bulk_create(receivers, batch_size=1000)
                
                return redirect('graphics_team:event_certificates', event_id)
            
            elif 'download_svg' in request.POST:
                certificate_id = request.POST.get('download_svg')
                certificate_template = Certificate_Template.objects.get(certificate_id=certificate_id)

                # File path on disk (e.g., from a FileField or stored path)
                file_path = certificate_template.svg_template.path

                if not os.path.exists(file_path):
                    raise Http404("File not found")

                # Read file and send as attachment
                with open(file_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/octet-stream')
                    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                    return response

        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file

        all_certificates_of_event = Certificate.objects.filter(event=event_id)

        context = {
            'user_data':user_data,
            'all_sc_ag':sc_ag,
            'all_certificates_of_event':all_certificates_of_event,
        }

        return render(request, "certificate/certificate_type_page.html", context)
    
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)

@login_required
@member_login_permission
def certificate_details(request, certificate_id):

    try:
        if request.method == 'POST':
            if 'add_receiver' in request.POST:
                name = request.POST.get('name')
                email = request.POST.get('email')

                Certificate_Receivers.objects.create(certificate_id=certificate_id, name=name, email=email)

                return redirect('graphics_team:certificate_details', certificate_id)

            elif 'add_csv' in request.POST:
                csv_file = request.FILES.get('csv_file')

                if Certificate_Receivers.objects.filter(certificate_id=certificate_id).exists():
                    Certificate_Receivers.objects.filter(certificate_id=certificate_id).delete()

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

                Certificate_Receivers.objects.bulk_create(receivers, batch_size=1000)

                return redirect('graphics_team:certificate_details', certificate_id)
            
            elif 'delete_receiver' in request.POST:
                receiver_id = request.POST.get('delete_receiver')

                Certificate_Receivers.objects.filter(id=receiver_id).delete()

                return redirect('graphics_team:certificate_details', certificate_id)

            elif 'download_receiver_certificate' in request.POST:
                # Get the object with the SVG FileField
                certificate_template = Certificate_Template.objects.get(certificate_id=certificate_id)
                svg_file = certificate_template.svg_template

                receiver_id = request.POST.get('download_receiver_certificate')
                receiver_name = Certificate_Receivers.objects.get(id=receiver_id).name

                svg_content = svg_file.read().decode('utf-8')
                tree = ET.ElementTree(ET.fromstring(svg_content))
                root = tree.getroot()
                ns = {'svg': 'http://www.w3.org/2000/svg'}

                # The text to search for
                old_text = 'Mirza Farhan Shahriar'

                # Loop over all <text> elements
                for text_elem in root.findall('.//svg:text', ns):                            
                    replace_text_in_element(text_elem, old_text, receiver_name)

                updated_svg = ET.tostring(root, encoding='unicode')

                # png_bytes = cairosvg.svg2png(
                #     bytestring=updated_svg.encode('utf-8'),
                #     background_color='white'  # remove transparency
                # )

                # response = HttpResponse(png_bytes, content_type='image/png')
                # response['Content-Disposition'] = 'attachment; filename="Certificate.png"'
                # return response
        
        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file

        certificate = Certificate.objects.get(id=certificate_id)
        event_name_of_certificate = Events.objects.values_list('event_name', flat=True).get(id=certificate.event_id)

        certificate_receivers = Certificate_Receivers.objects.filter(certificate_id=certificate_id)

        context = {
            'user_data':user_data,
            'all_sc_ag':sc_ag,
            'certificate':certificate,
            'event_name':event_name_of_certificate,
            'certificate_receivers':certificate_receivers,
        }    

        return render(request, "certificate/certificate_details_page.html", context)
    
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return cv.custom_500(request)

@login_required
@member_login_permission
def certificate_otp(request):
    return render(request, "certificate/certificate_otp.html")


@login_required
@member_login_permission
def certificate_download(request):
    return render(request, "certificate/certificate_download.html")

@login_required
@member_login_permission
def certificate_email(request):
    return render(request, "certificate/certificate_email.html")


# def download_file(request, certificate_id):
#     if request.method == "POST":
#         # Get the certificate object
#         certificate = get_object_or_404(Certificate, pk=certificate_id)

#         # File path on disk (e.g., from a FileField or stored path)
#         file_path = certificate.file.path  # or certificate.file_url if stored differently

#         if not os.path.exists(file_path):
#             raise Http404("File not found")

#         # Read file and send as attachment
#         with open(file_path, 'rb') as f:
#             response = HttpResponse(f.read(), content_type='application/octet-stream')
#             response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
#             return response

#     # Block GET requests
#     return Http404("Invalid request")

def replace_text_in_element(element, old_text, new_text):
    """
    Recursively searches element text and children to replace old_text with new_text.
    """
    if element.text and old_text in element.text:
        element.text = element.text.replace(old_text, new_text)
    for child in element:
        replace_text_in_element(child, old_text, new_text)
        if child.tail and old_text in child.tail:
            child.tail = child.tail.replace(old_text, new_text)