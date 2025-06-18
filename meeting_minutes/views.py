from django.shortcuts import get_object_or_404, redirect, render

from central_branch import renderData
from meeting_minutes.models import MeetingMinutes
from django.views.decorators.csrf import csrf_exempt
# from . import renderData
# from meeting_minutes.renderData import team_mm_info,branch_mm_info

# Create your views here.
def meeting_minutes_homepage(request):
    return render(request,'meeting_minutes_homepage.html')

def team_meeting_minutes(request):
    '''
    Loads all the teams' exisitng meeting minutes
    Gives option to add or delete a meeting minutes
    '''
    
    #load teams' meeting minutes from database
    
    teams_mm=renderData.team_meeting_minutes.load_all_team_mm()
    team_mm_list=[]
    for team in teams_mm:
        team_mm_list.append(team)
    context={
        'team':team_mm_list
    }

    return render(request,'team_meeting_minutes.html')


def branch_meeting_minutes(request):
    '''
    Loads all the branchs' existing meeting minutes
    Gives option to add or delete a meeting minutes
    '''
    
    #load branchs' meeting minutes from database
    
    branch_mm=renderData.branch_meeting_minutes.load_all_branch_mm()
    branch_mm_list=[]
    for branch in branch_mm:
        branch_mm_list.append(branch)
    context={
        'team':branch_mm_list
    }
    return render(request,'branch_meeting_minutes.html')


    #meeting_minutes_edit
def meeting_minutes_edit(request):
    return render(request, 'meeting_minutes_edit.html')


def meeting_minutes_edit(request, pk=None):
    if pk:
        meeting = get_object_or_404(MeetingMinutes, pk=pk)  # Edit mode
    else:
        meeting = None  # Create mode

    if request.method == 'POST':
        # Extract values from form fields
        location = request.POST.get('location')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        venue = request.POST.get('venue')
        total_attendee = request.POST.get('total_attendee')
        ieee_attendee = request.POST.get('ieee_attendee')
        non_ieee_attendee = request.POST.get('non_ieee_attendee')
        agendas = request.POST.getlist('agenda[]')
        discussion = request.POST.get('discussion')
        host = request.POST.get('host')
        co_host = request.POST.get('co_host')
        guest = request.POST.get('guest')
        written_by = request.POST.get('written_by')

        if meeting:
            # Update existing
            meeting.location = location
            meeting.start_time = start_time
            meeting.end_time = end_time
            meeting.venue = venue
            meeting.total_attendee = total_attendee
            meeting.ieee_attendee = ieee_attendee
            meeting.non_ieee_attendee = non_ieee_attendee
            meeting.agenda = agendas
            meeting.discussion = discussion
            meeting.host = host
            meeting.co_host = co_host
            meeting.guest = guest
            meeting.written_by = written_by
            meeting.save()
        else:
            # Create new
            MeetingMinutes.objects.create(
                location=location,
                start_time=start_time,
                end_time=end_time,
                venue=venue,
                total_attendee=total_attendee,
                ieee_attendee=ieee_attendee,
                non_ieee_attendee=non_ieee_attendee,
                agenda=agendas,
                discussion=discussion,
                host=host,
                co_host=co_host,
                guest=guest,
                written_by=written_by
            )

        return redirect("meeting_minutes:meeting_minutes_homepage")

    return render(request, 'meeting_minutes_edit.html', {
        'meeting': meeting
    })