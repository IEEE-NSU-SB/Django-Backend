from datetime import datetime, time
import logging
import traceback
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
import os
from central_branch.renderData import Branch
from central_branch.views import custom_500
from chapters_and_affinity_group.get_sc_ag_info import SC_AG_Info
from finance_and_corporate_team.genPDF import BudgetPDF
from main_website.models import Toolkit
from meeting_minutes.manage_access import MM_Render_Access
from port.models import Chapters_Society_and_Affinity_Groups, Teams
from system_administration.system_error_handling import ErrorHandling
from users import renderData
from insb_port import settings
from meeting_minutes.models import MeetingMinutes, MeetingMinutesAccess
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from users.models import Members, Panel_Members
from users.renderData import member_login_permission
from django.contrib.auth.decorators import login_required
from django.utils.html import strip_tags
from django.db.models import OuterRef, Subquery
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY

from port.renderData import PortData
# from . import renderData

# Create your views here.
logger=logging.getLogger(__name__) 

@login_required
@member_login_permission
def meeting_minutes_homepage(request, primary=None, team_primary=None):

    try:
        
        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        get_sc_ag_info=None
        
        has_access = MM_Render_Access.has_meeting_minutes_homepage_access(request, sc_ag_primary=(primary if primary != None else 1), team_primary=team_primary)

        if has_access:
            if primary:
                meetings = MeetingMinutes.objects.filter(sc_ag__primary=primary).order_by('-meeting_date')
                get_sc_ag_info = SC_AG_Info.get_sc_ag_details(request,primary)
                has_meeting_minutes_create_access = MM_Render_Access.has_meeting_minutes_create_access(request, sc_ag_primary=primary)
            else:
                primary = 1
                if team_primary is not None:
                    meetings = MeetingMinutes.objects.filter(sc_ag__primary=1, team__primary=team_primary).order_by('-meeting_date')
                    has_meeting_minutes_create_access = MM_Render_Access.has_meeting_minutes_create_access(request, sc_ag_primary=1, team_primary=team_primary)
                else:
                    meetings = MeetingMinutes.objects.filter(sc_ag__primary=1, team__primary=1).order_by('-meeting_date')
                    has_meeting_minutes_create_access = MM_Render_Access.has_meeting_minutes_create_access(request, sc_ag_primary=1)

            team_namespace = None
            create_url = None
            edit_url = None
            if team_primary != None:
                team_namespace = get_team_redirect_namespace(team_primary)
                create_url = f'{team_namespace}:meeting_minutes_create_team'
                edit_url = f'{team_namespace}:meeting_minutes_edit_team'        
            
            context = {
                'all_sc_ag':sc_ag,
                'sc_ag_info':get_sc_ag_info,
                'user_data':user_data,
                'has_meeting_minutes_create_access':has_meeting_minutes_create_access,
                'primary': primary,
                'team_primary':team_primary,
                'team_namespace':team_namespace,
                'create_url':create_url,
                'edit_url':edit_url,
                'meetings': meetings,
            }
            return render(request, 'meeting_minutes_homepage.html', context)
        
        else:
            return render(request,'access_denied.html', {'all_sc_ag':sc_ag,'user_data':user_data,'sc_ag_info':get_sc_ag_info})
    
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return custom_500(request)

@login_required
@member_login_permission
def meeting_minutes_create(request, primary=None, team_primary=None):

    try:
        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        get_sc_ag_info=None
        
        has_access = MM_Render_Access.has_meeting_minutes_create_access(request, sc_ag_primary=(primary if primary != None else 1), team_primary=team_primary)
        
        if has_access:
            team_namespace = None
            homepage_url = None
            if team_primary != None:
                team_namespace = get_team_redirect_namespace(team_primary)
                homepage_url = f'{team_namespace}:meeting_minutes_homepage_team'

            if request.method == 'POST':
                location = request.POST.get('location')
                start_time = request.POST.get('start_time')
                end_time = request.POST.get('end_time')
                meeting_date = request.POST.get('meeting_date')
                selected_team = request.POST.get('selected_team')
                
                venue = request.POST.get('venue')
                total_attendee = int(request.POST.get('total_attendees', 0) or 0)
                ieee_attendee = int(request.POST.get('ieee_attendee', 0) or 0)
                non_ieee_attendee = int(request.POST.get('non_ieee_attendee', 0) or 0)
                agendas = request.POST.getlist('agenda[]')
                discussion = request.POST.get('discussion')
                host = request.POST.get('host')
                co_host = request.POST.get('co_host')
                guest = request.POST.get('guest')
                written_by = request.POST.get('written_by')
                meeting_name = request.POST.get('meeting_name')
                
                if selected_team == None:
                    selected_team = 1

                if primary:
                    sc_ag = Chapters_Society_and_Affinity_Groups.objects.filter(primary=primary).values('id')[0]['id']
                    team = Teams.objects.filter(team_of__primary=primary, primary=selected_team).values('id')[0]['id']
                else:
                    sc_ag = Chapters_Society_and_Affinity_Groups.objects.filter(primary=1).values('id')[0]['id']
                    team = Teams.objects.filter(team_of__primary=1, primary=selected_team).values('id')[0]['id']

                meeting_minutes = MeetingMinutes.objects.create(
                    sc_ag_id=sc_ag,
                    team_id=team,
                    meeting_name=meeting_name,
                    location=location,
                    start_time=start_time,
                    end_time=end_time,
                    meeting_date=meeting_date,
                    venue=venue,
                    total_attendee=total_attendee,
                    ieee_attendee=ieee_attendee,
                    non_ieee_attendee=non_ieee_attendee,
                    agendas=agendas,
                    discussion=discussion,
                    host=host,
                    co_host=co_host,
                    guest=guest,
                    written_by=written_by
                )
                
                try: 
                    username = request.user.username
                    member = Members.objects.get(ieee_id=username)
                    MeetingMinutesAccess.objects.create(meeting_minutes=meeting_minutes, member=member, access_type='Edit')
                except:
                    pass

                if primary:
                    return redirect('chapters_and_affinity_group:meeting_minutes:meeting_minutes_homepage', primary)
                else:
                    if team_primary != None:
                        return redirect(homepage_url, team_primary)
                    else:
                        return redirect('central_branch:meeting_minutes:meeting_minutes_homepage')
            

            if primary:
                get_sc_ag_info = SC_AG_Info.get_sc_ag_details(request,primary)
                teams = Teams.objects.filter(team_of__primary=primary, is_active=True).values('primary', 'team_name')
            else:
                primary = 1
                teams = Teams.objects.filter(team_of__primary=1, is_active=True).values('primary', 'team_name')

            context = {
                'all_sc_ag':sc_ag,
                'sc_ag_info':get_sc_ag_info,
                'user_data':user_data,
                'primary': primary,
                'team_primary':team_primary,
                'team_namespace':team_namespace,
                'homepage_url':homepage_url,
                'teams':teams,
                'meeting': None,
                'has_access':'Edit'
            }

            return render(request, 'meeting_minutes_edit.html', context)

        else:
            return render(request,'access_denied.html', {'all_sc_ag':sc_ag,'user_data':user_data,'sc_ag_info':get_sc_ag_info})
    
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return custom_500(request)

@login_required
@member_login_permission
def meeting_minutes_edit(request, pk, primary=None, team_primary=None):

    try:

        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        get_sc_ag_info=None

        has_access = MM_Render_Access.has_meeting_minutes_access(request, pk, sc_ag_primary=(primary if primary != None else 1), team_primary=team_primary)

        if has_access != 'Restricted':       
            meeting = MeetingMinutes.objects.get(pk=pk)

            if request.method == 'POST':
                edit_url = None
                if team_primary != None:
                    team_namespace = get_team_redirect_namespace(team_primary)
                    edit_url = f'{team_namespace}:meeting_minutes_edit_team'

                if 'save' in request.POST:

                    location = request.POST.get('location')
                    start_time = request.POST.get('start_time')
                    end_time = request.POST.get('end_time')

                    meeting.meeting_date=request.POST.get('meeting_date')
                    meeting.meeting_name = request.POST.get('meeting_name')
                    meeting.location = location
                    meeting.start_time = start_time
                    meeting.end_time = end_time
                    meeting.venue = request.POST.get('venue')
                    meeting.total_attendee = int(request.POST.get('total_attendees', 0))
                    meeting.ieee_attendee = request.POST.get('ieee_attendee')
                    meeting.non_ieee_attendee = request.POST.get('non_ieee_attendee')
                    meeting.agendas = request.POST.getlist('agenda[]')
                    meeting.discussion = request.POST.get('discussion')
                    meeting.host = request.POST.get('host')
                    meeting.co_host = request.POST.get('co_host')
                    meeting.guest = request.POST.get('guest')
                    meeting.written_by = request.POST.get('written_by')
                    
                    meeting.save()
                    
                elif 'save_access' in request.POST:
                    ieee_ids = request.POST.getlist('ieee_id')
                    access_types = request.POST.getlist('access_type')

                    for i in range(len(ieee_ids)):
                        access = MeetingMinutesAccess.objects.filter(meeting_minutes_id=pk, member=ieee_ids[i])
                        if access.exists():
                            if access_types[i] != '':
                                access.update(access_type=access_types[i])
                            else:
                                access.delete()
                        else:
                            if access_types[i] != '':
                                MeetingMinutesAccess.objects.create(meeting_minutes_id=pk, member=Members.objects.get(ieee_id=ieee_ids[i]), access_type=access_types[i])

                elif 'delete' in request.POST:
                    meeting.delete()
                    if primary:
                        return redirect('chapters_and_affinity_group:meeting_minutes:meeting_minutes_homepage', primary)
                    else:
                        if team_primary is not None:
                            team_namespace = get_team_redirect_namespace(team_primary)
                            return redirect(f'{team_namespace}:meeting_minutes_homepage_team', team_primary)
                        else:
                            return redirect('central_branch:meeting_minutes:meeting_minutes_homepage')   
                    
                    

                if primary:
                    return redirect('chapters_and_affinity_group:meeting_minutes:meeting_minutes_edit', primary, pk)
                else:
                    if team_primary != None:
                        redirect(edit_url, team_primary, pk)
                    else:
                        return redirect('central_branch:meeting_minutes:meeting_minutes_edit', pk)
            

            if primary:
                get_sc_ag_info = SC_AG_Info.get_sc_ag_details(request,primary)
                teams = Teams.objects.filter(team_of__primary=primary).values('primary', 'team_name')
                current_panel = SC_AG_Info.get_current_panel_of_sc_ag(request, sc_ag_primary=primary)
                # Subquery to get the access_type for the matching member
                access_qs = MeetingMinutesAccess.objects.filter(
                    member=OuterRef('member'),
                    meeting_minutes=pk
                ).values('access_type')[:1]  # get first match only

                # Main query: Panel_Members with access_type annotated
                members = Panel_Members.objects.filter(tenure=current_panel[0]).annotate(
                    access_type=Subquery(access_qs)
                )
            else:
                primary = 1
                teams = Teams.objects.filter(team_of__primary=1).values('primary', 'team_name')
                current_panel = Branch.load_current_panel()

                if team_primary != None:
                    # Subquery to get the access_type for the matching member
                    access_qs = MeetingMinutesAccess.objects.filter(
                        member=OuterRef('member'),
                        meeting_minutes=pk
                    ).values('access_type')[:1]  # get first match only

                    # Main query: Panel_Members with access_type annotated
                    members = Panel_Members.objects.filter(tenure=current_panel, team__primary=team_primary).annotate(
                        access_type=Subquery(access_qs)
                    )
                else:
                    # Subquery to get the access_type for the matching member
                    access_qs = MeetingMinutesAccess.objects.filter(
                        member=OuterRef('member'),
                        meeting_minutes=pk
                    ).values('access_type')[:1]  # get first match only

                    # Main query: Panel_Members with access_type annotated
                    members = Panel_Members.objects.filter(tenure=current_panel).annotate(
                        access_type=Subquery(access_qs)
                    )

            team_namespace = None
            homepage_url = None
            if team_primary != None:
                team_namespace = get_team_redirect_namespace(team_primary)
                homepage_url = f'{team_namespace}:meeting_minutes_homepage_team'

            context = {
                'all_sc_ag':sc_ag,
                'sc_ag_info':get_sc_ag_info,
                'user_data':user_data,
                'primary': primary,
                'team_primary':team_primary,
                'team_namespace':team_namespace,
                'homepage_url':homepage_url,
                'teams':teams,
                'meeting': meeting,
                'members':members,
                'has_access':has_access
            }

            return render(request, 'meeting_minutes_edit.html', context)

        else:
            return render(request,'access_denied.html', {'all_sc_ag':sc_ag,'user_data':user_data,'sc_ag_info':get_sc_ag_info})
    
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return custom_500(request)

@login_required
@member_login_permission
def download_meeting_pdf(request, pk, primary=None):
    try:
        # Fetch the meeting object
        meeting = get_object_or_404(MeetingMinutes, pk=pk)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="meeting_{pk}.pdf"'

        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        margin = 50
        line_height = 20
        y = height - 60


        p.setFont("Helvetica-Bold", 20)
        p.setFillColor(colors.darkblue)
        if primary and int(primary) == 1:
            p.drawCentredString(width / 2, y, "IEEE NSU Student Branch")
        else:
            branch_name = get_branch_name(int(primary))
            p.drawCentredString(width / 2, y, branch_name)
        y -= 25
        
        p.setFont("Helvetica-Bold", 16)
        p.setFillColor(colors.black)
        p.drawCentredString(width / 2, y, "Meeting Minutes")
        y -= 35
        
        branch_logo = Toolkit.objects.get(title=get_sc_ag_logo_name(1)).picture
        branch_logo_path = settings.MEDIA_ROOT+str(branch_logo)
        sc_ag_logo_path = None
        
        try:
            # Only draw Branch logo if primary != 1
            if primary and int(primary) != 1:
                sc_ag_logo = Toolkit.objects.get(title=get_sc_ag_logo_name(int(primary))).picture
                sc_ag_logo_path = settings.MEDIA_ROOT+str(sc_ag_logo)
                print("Test:",primary)

                if os.path.exists(sc_ag_logo_path):
                    p.drawImage(
                        ImageReader(sc_ag_logo_path),
                        x=margin,
                        y=height - 90,
                        width=50,
                        height=50,
                        preserveAspectRatio=True,
                        mask='auto'
                    )      

        except Exception as e:
            logger.warning(f"Branch logo could not be loaded: {e}")
            
        try:
            if os.path.exists(branch_logo_path):
                p.drawImage(
                    ImageReader(branch_logo_path),
                    x=width - margin - 50,
                    y=height - 90,
                    width=50,
                    height=50,
                    preserveAspectRatio=True,
                    mask='auto'
                )
        except Exception as e:
            logger.warning(f"Main Branch logo could not be loaded: {e}")    
        
        
        y -= 20
        p.setStrokeColor(colors.darkblue)
        p.setLineWidth(3)
        p.line(margin, y, width - margin, y)
        y -= 30

        def draw_field(label, value, is_bold=False):
            nonlocal y
            font = "Helvetica-Bold" if is_bold else "Helvetica"
            p.setFont(font, 11)
            p.drawString(margin, y, f"{label}:")
            p.setFont("Helvetica", 11)
            p.drawString(margin + 120, y, str(value))
            y -= line_height

        draw_field("Meeting Name", meeting.meeting_name or "N/A", True)
        draw_field("Date", meeting.meeting_date.strftime("%B %d, %Y") if meeting.meeting_date else "N/A")
        draw_field("Time", f"{meeting.start_time.strftime('%I:%M %p')} - {meeting.end_time.strftime('%I:%M %p')}"
                  if meeting.start_time and meeting.end_time else "N/A")
        draw_field("Location", meeting.location or "N/A")
        draw_field("Venue", meeting.venue or "N/A")
        
        y -= 10
        
        total = meeting.total_attendee or 0
        ieee = meeting.ieee_attendee or 0
        non_ieee = meeting.non_ieee_attendee or 0
        draw_field("Attendance", f"Total: {total} (IEEE: {ieee}, Non-IEEE: {non_ieee})", True)
        
        y -= 10
        
        draw_field("Host", meeting.host or "N/A")
        draw_field("Co-host", meeting.co_host or "N/A")
        draw_field("Guest", meeting.guest or "N/A")
        draw_field("Written by", meeting.written_by or "N/A")
        
        y -= 15
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(margin, y, "Agenda:")
        y -= line_height
        p.setFont("Helvetica", 10)
        agenda_text = ", ".join(meeting.agendas) if isinstance(meeting.agendas, list) else (meeting.agendas or "N/A")
        
        words = agenda_text.split()
        line = ""
        for word in words:
            if p.stringWidth(line + word, "Helvetica", 10) < width - 2 * margin:
                line += word + " "
            else:
                p.drawString(margin + 20, y, line.strip())
                y -= 15
                line = word + " "
        if line:
            p.drawString(margin + 20, y, line.strip())
            y -= 25

        p.setFont("Helvetica-Bold", 12)
        p.drawString(margin, y, "Discussion:")
        y -= line_height
        
        # Create justified paragraph style
        justified_style = ParagraphStyle(
            'Justified',
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            leftIndent=20,
            rightIndent=20,
            spaceAfter=10
        )
        
        # Discussion text formatted as justified paragraphs
        discussion_text = strip_tags(meeting.discussion or "No discussion recorded.")
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in discussion_text.replace('\r\n', '\n').split('\n') if p.strip()]
        
        def check_new_page(needed_height=50):
            nonlocal y
            if y < needed_height:
                p.showPage()
                y = height - 60
                p.setFont("Helvetica-Bold", 12)
                p.setFillColor(colors.darkblue)
                p.drawString(margin, y, "Discussion (continued):")
                y -= line_height + 10
                p.setFillColor(colors.black)

        for paragraph_text in paragraphs:
            para = Paragraph(paragraph_text, justified_style)
            para_width = width - 2 * margin 
            para_height = para.wrap(para_width, y)[1]
            check_new_page(para_height) 
            para.drawOn(p, margin, y - para_height)
            y -= para_height + 10

        if y < 80:
            p.showPage()
            y = height - 60

        p.saveState()
        p.setFont("Helvetica", 50)
        p.setFillColor(colors.lightgrey)
        p.setFillAlpha(0.1)
        p.translate(width/2, height/2)
        p.rotate(45)
        p.drawCentredString(0, 0, "IEEE NSU")
        p.restoreState()
        p.setFont("Helvetica", 8)
        p.setFillColor(colors.gray)
        p.drawCentredString(width / 2, 30, f"Generated on {datetime.now().strftime('%B %d, %Y')}")

        p.save()
        return response

    except Exception as e:
        logger.error(f"Error generating meeting PDF at {datetime.now()}", exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e, error_traceback=traceback.format_exc())
        return HttpResponse("Internal Server Error while generating PDF.", status=500)

def get_team_redirect_namespace(team_primary):

    if team_primary == 2:
        return 'content_writing_and_publications_team'
    elif team_primary == 3:
        return 'events_and_management_team'
    elif team_primary == 4:
        return 'logistics_and_operations_team'
    elif team_primary == 5:
        return 'promotions_team'
    elif team_primary == 6 or team_primary == 0:
        return 'public_relation_team'
    elif team_primary == 7:
        return 'membership_development_team'
    elif team_primary == 8:
        return 'website_development_team'
    elif team_primary == 9:
        return 'media_team'
    elif team_primary == 10:
        return 'graphics_team'
    elif team_primary == 11:
        return 'finance_and_corporate_team'
    
def get_sc_ag_logo_name(sc_primary):
        if sc_primary == 1:
            return 'IEEE NSU SB Logo'
        elif sc_primary == 2:
            return 'IEEE NSU PES SBC Logo'
        elif sc_primary == 3:
            return 'IEEE NSU RAS SBC Logo'
        elif sc_primary == 4:
            return 'IEEE NSU IAS SBC Logo'
        elif sc_primary == 5:
            return 'IEEE NSU SB WIE AG Logo'
        
def get_sc_ag_header_color(primary):
        if primary == 1:
            return '#137AAC'
        elif primary == 2:
            return '#659941'
        elif primary == 3:
            return '#602569'
        elif primary == 4:
            return '#008bC2'
        elif primary == 5:
            return '#006699'    
        
        
def get_branch_name(sc_primary):
    branch_names = {
        2: "IEEE NSU Power and Energy Society",
        3: "IEEE NSU Robotics and Automation Society",
        4: "IEEE NSU Industry Application Society",
        5: "IEEE NSU Women in Engineering Affinity Group",
    }
    return branch_names.get(sc_primary, "Unknown Branch")