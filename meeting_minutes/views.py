from datetime import datetime, time
import logging
import traceback
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
import os
from central_branch.renderData import Branch
from central_branch.views import custom_500
from chapters_and_affinity_group.get_sc_ag_info import SC_AG_Info
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
                    meetings = MeetingMinutes.objects.filter(sc_ag__primary=1, team__primary=None).order_by('-meeting_date')
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
                teams = Teams.objects.filter(team_of__primary=primary).values('primary', 'team_name')
            else:
                primary = 1
                teams = Teams.objects.filter(team_of__primary=1).values('primary', 'team_name')

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
def download_meeting_pdf(request, pk):
    try:
        # Fetch the meeting object
        meeting = get_object_or_404(MeetingMinutes, pk=pk)

        # Set up HTTP response headers for PDF download
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="meeting_{pk}.pdf"'

        # Create the PDF canvas
        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        # Define margins and spacing
        top_margin = 50
        left_margin = 50
        line_height = 20
        y = height - top_margin

        # Draw Logo if it exists
        try:
            logo_path = os.path.join(settings.BASE_DIR, 'meeting_minutes', 'static', 'images', 'logo.jpg')
            if os.path.exists(logo_path):
                p.drawImage(
                    ImageReader(logo_path),
                    x=width - 130,
                    y=height - 130,
                    width=80,
                    height=80,
                    preserveAspectRatio=True,
                    mask='auto'
                )
        except Exception as e:
            logger.warning(f"Logo could not be loaded: {e}")

        # Draw Watermark
        p.saveState()
        p.setFont("Helvetica-Bold", 40)
        p.setFillGray(0.9)
        p.drawCentredString(width / 2, height / 2, "IEEE NSU Student Branch")
        p.restoreState()

        # Draw Title
        p.setFont("Helvetica-Bold", 24)
        p.drawCentredString(width / 2, y, "Meeting Minutes Report")
        y -= 2 * line_height

        # Helper to draw lines
        def draw_line(label, value):
            nonlocal y
            if y < 50:
                p.showPage()
                y = height - top_margin
            p.setFont("Helvetica", 14)
            p.drawString(left_margin, y, f"{label}: {value}")
            y -= line_height

        # Add meeting fields
        draw_line("Meeting Name", meeting.meeting_name or "N/A")
        draw_line("Date", meeting.meeting_date.strftime("%Y-%m-%d") if meeting.meeting_date else "N/A")
        draw_line(
            "Time",
            f"{meeting.start_time.strftime('%H:%M')} - {meeting.end_time.strftime('%H:%M')}"
            if meeting.start_time and meeting.end_time else "N/A"
        )
        draw_line("Location", meeting.location or "N/A")
        draw_line("Venue", meeting.venue or "N/A")
        draw_line("Total Attendees", str(meeting.total_attendee or 0))
        draw_line("IEEE Attendees", str(meeting.ieee_attendee or 0))
        draw_line("Non-IEEE Attendees", str(meeting.non_ieee_attendee or 0))
        draw_line("Agendas", ", ".join(meeting.agendas) if isinstance(meeting.agendas, list) else (meeting.agendas or "N/A"))
        draw_line("Host", meeting.host or "N/A")
        draw_line("Co-host", meeting.co_host or "N/A")
        draw_line("Guest", meeting.guest or "N/A")
        draw_line("Written by", meeting.written_by or "N/A")

        # Discussion Section (multi-line)
        y -= line_height
        p.setFont("Helvetica-Bold", 16)
        p.drawString(left_margin, y, "Discussion:")
        y -= line_height

        p.setFont("Helvetica", 12)
        text_object = p.beginText(left_margin, y)
        discussion_lines = strip_tags(meeting.discussion or "N/A").splitlines()
        for line in discussion_lines:
            text_object.textLine(line)
        p.drawText(text_object)

        # Finish PDF
        p.showPage()
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