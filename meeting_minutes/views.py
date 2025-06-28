from datetime import datetime, time
import logging
import traceback
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
import os
from central_branch.views import custom_500
from chapters_and_affinity_group.get_sc_ag_info import SC_AG_Info
from port.models import Chapters_Society_and_Affinity_Groups
from system_administration.system_error_handling import ErrorHandling
from users import renderData
from insb_port import settings
from meeting_minutes.models import MeetingMinutes
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from users.renderData import member_login_permission
from django.contrib.auth.decorators import login_required

from port.renderData import PortData
# from . import renderData

# Create your views here.
logger=logging.getLogger(__name__) 

# def team_meeting_minutes(request):
#     '''
#     Loads all the teams' exisitng meeting minutes
#     Gives option to add or delete a meeting minutes
#     '''
     
#     #load teams' meeting minutes from database
    
#     teams_mm=renderData.team_meeting_minutes.load_all_team_mm()
#     team_mm_list=[]
#     for team in teams_mm:
#         team_mm_list.append(team)
#     context={
#         'team':team_mm_list
#     }

#     return render(request,'team_meeting_minutes.html')


# def branch_meeting_minutes(request):
#     '''
#     Loads all the branchs' existing meeting minutes
#     Gives option to add or delete a meeting minutes
#     '''
    
#     #load branchs' meeting minutes from database
    
#     branch_mm=renderData.branch_meeting_minutes.load_all_branch_mm()
#     branch_mm_list=[]
#     for branch in branch_mm:
#         branch_mm_list.append(branch)
#     context={
#         'team':branch_mm_list
#     }
#     return render(request,'branch_meeting_minutes.html')


@login_required
@member_login_permission
def meeting_minutes_homepage(request, primary=None):

    try:
        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        get_sc_ag_info=None
        
        if primary:
            meetings = MeetingMinutes.objects.filter(sc_ag__primary=primary).order_by('-meeting_date')
            get_sc_ag_info = SC_AG_Info.get_sc_ag_details(request,primary)
        else:
            primary = 1
            meetings = MeetingMinutes.objects.filter(sc_ag__primary=1).order_by('-meeting_date')
        
        context = {
            'all_sc_ag':sc_ag,
            'sc_ag_info':get_sc_ag_info,
            'user_data':user_data,
            'primary': primary,
            'meetings': meetings,
        }
        return render(request, 'meeting_minutes_homepage.html', context)
    
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return custom_500(request)

@login_required
@member_login_permission
def meeting_minutes_create(request, primary=None):

    try:
        if request.method == 'POST':
            location = request.POST.get('location')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            meeting_date=request.POST.get('meeting_date')
            
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
            else:
                sc_ag = Chapters_Society_and_Affinity_Groups.objects.filter(primary=1).values('id')[0]['id']

            MeetingMinutes.objects.create(
                sc_ag_id=sc_ag,
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

            if primary:
                return redirect('chapters_and_affinity_group:meeting_minutes:meeting_minutes_homepage', primary)
            else:
                return redirect('central_branch:meeting_minutes:meeting_minutes_homepage')
        
        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        get_sc_ag_info=None

        if primary:
            get_sc_ag_info = SC_AG_Info.get_sc_ag_details(request,primary)
        else:
            primary = 1

        context = {
            'all_sc_ag':sc_ag,
            'sc_ag_info':get_sc_ag_info,
            'user_data':user_data,
            'primary': primary,
            'meeting': None
        }

        return render(request, 'meeting_minutes_edit.html', context)
    
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return custom_500(request)

@login_required
@member_login_permission
def meeting_minutes_edit(request, pk, primary=None):

    try:
        meeting = MeetingMinutes.objects.get(pk=pk)

        if request.method == 'POST':
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
                
            elif 'delete' in request.POST:
                meeting.delete()

            if primary:
                return redirect('chapters_and_affinity_group:meeting_minutes:meeting_minutes_edit', primary, pk)
            else:
                return redirect('central_branch:meeting_minutes:meeting_minutes_edit', pk)
        
        sc_ag=PortData.get_all_sc_ag(request=request)
        current_user=renderData.LoggedinUser(request.user) #Creating an Object of logged in user with current users credentials
        user_data=current_user.getUserData() #getting user data as dictionary file
        get_sc_ag_info=None

        if primary:
            get_sc_ag_info = SC_AG_Info.get_sc_ag_details(request,primary)
        else:
            primary = 1

        context = {
            'all_sc_ag':sc_ag,
            'sc_ag_info':get_sc_ag_info,
            'user_data':user_data,
            'primary': primary,
            'meeting': meeting,
        }

        return render(request, 'meeting_minutes_edit.html', context)
    
    except Exception as e:
        logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
        ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
        return custom_500(request)

@login_required
def download_meeting_pdf(request, pk):
    # Try to fetch the meeting by primary key
    try:
        meeting = MeetingMinutes.objects.get(pk=pk)
    except MeetingMinutes.DoesNotExist:
        return HttpResponse("Meeting not found.", status=404)

    # Set up HTTP response headers for PDF download
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="meeting_{pk}.pdf"'

    # Create a canvas object for drawing the PDF
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4  # Page size

    # Start position from the top of the page
    y = height - 100
    line_height = 30  # Space between lines
    
    logo_path = os.path.join(settings.BASE_DIR, 'meeting_minutes', 'static', 'images', 'logo.jpg')  
    if os.path.exists(logo_path):
        p.drawImage(
    ImageReader(logo_path),
    x=500, y=height - 100,  # Position
    width=80, height=80,   # Size
    preserveAspectRatio=True,
    mask='auto'            
)
        
    print("LOGO PATH:", logo_path)
    print("Exists:", os.path.exists(logo_path))    

   
    p.saveState()
    p.setFont("Helvetica", 40)
    p.setFillColorRGB(0.7, 0.9, 1.0, alpha=0.5)
    p.drawCentredString(width / 2, height / 2, "IEEE NSU Student Branch")
    p.restoreState()

    # Helper function to draw each field in the PDF
    def draw_line(label, value):
        nonlocal y
        p.setFont("Helvetica", 16)
        p.drawString(50, y, f"{label}: {value}")
        y -= line_height

   # Write meeting fields to PDF
    draw_line("Meeting Name", meeting.meeting_name)
    draw_line("Date", meeting.meeting_date.strftime("%Y-%m-%d"))
    draw_line("Time", f"{meeting.start_time.strftime('%H:%M')} - {meeting.end_time.strftime('%H:%M')}")
    draw_line("Location", meeting.location)
    draw_line("Venue", meeting.venue or "N/A")
    draw_line("Total Attendees", str(meeting.total_attendee))
    draw_line("IEEE Attendees", str(meeting.ieee_attendee) if meeting.ieee_attendee is not None else "N/A")
    draw_line("Non-IEEE Attendees", str(meeting.non_ieee_attendee) if meeting.non_ieee_attendee is not None else "N/A")
    draw_line("Agendas", meeting.agendas)
    
    draw_line("Host", meeting.host or "N/A")
    draw_line("Co-host", meeting.co_host or "N/A")
    draw_line("Guest", meeting.guest or "N/A")
    draw_line("Written by", meeting.written_by)
    # Add the "Discussion" section
    p.drawString(50, y, "Discussion:")
    y -= line_height

    # Begin text block for discussion content (multi-line)
    text_object = p.beginText(50, y)
    text_object.setFont("Helvetica", 12)

    # Write each line of discussion to the PDF
    for line in meeting.discussion.splitlines():
        text_object.textLine(line)

    p.drawText(text_object)

    # Finalize and close the PDF document
    p.showPage()
    p.save()

    # Return the response as a downloadable PDF
    return response