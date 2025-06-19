from datetime import datetime, time
from django.shortcuts import get_object_or_404, redirect, render

from central_branch import renderData
from meeting_minutes.models import MeetingMinutes
from django.views.decorators.csrf import csrf_exempt
# from . import renderData
# from meeting_minutes.renderData import team_mm_info,branch_mm_info

# Create your views here.
def meeting_minutes_homepage(request):
    meetings = MeetingMinutes.objects.all().order_by('-date')
    return render(request, 'meeting_minutes_homepage.html', {'meetings': meetings})

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




def meeting_minutes_create(request):
    if request.method == 'POST':
        location = request.POST.get('location')
        start_time_raw = request.POST.get('start_time')
        end_time_raw = request.POST.get('end_time')

        if 'T' in start_time_raw:
            dt_obj = datetime.fromisoformat(start_time_raw)
            date = dt_obj.date()
            start_time = dt_obj.time()
        else:
            date = datetime.today().date()
            start_time = datetime.strptime(start_time_raw, '%H:%M').time()

        if 'T' in end_time_raw:
            end_time = datetime.fromisoformat(end_time_raw).time()
        else:
            end_time = datetime.strptime(end_time_raw, '%H:%M').time()
        venue = request.POST.get('venue')
        total_attendee = int(request.POST.get('total_attendees', 0))
        ieee_attendee = request.POST.get('ieee_attendee')
        non_ieee_attendee = request.POST.get('non_ieee_attendee')
        agendas = request.POST.getlist('agenda[]')
        discussion = request.POST.get('discussion')
        host = request.POST.get('host')
        co_host = request.POST.get('co_host')
        guest = request.POST.get('guest')
        written_by = request.POST.get('written_by')
        meeting_name = request.POST.get('meeting_name')

        MeetingMinutes.objects.create(
            meeting_name=meeting_name,
            location=location,
            start_time=start_time,
            end_time=end_time,
            date=date,
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

        return redirect('meeting_minutes:meeting_minutes_homepage')

    return render(request, 'meeting_minutes_edit.html', {'meeting': None})


def meeting_minutes_edit(request, pk):
    meeting = get_object_or_404(MeetingMinutes, pk=pk)

    if request.method == 'POST':
        location = request.POST.get('location')
        start_time_raw = request.POST.get('start_time')
        end_time_raw = request.POST.get('end_time')

        start_time = datetime.fromisoformat(start_time_raw).time() if 'T' in start_time_raw else datetime.strptime(start_time_raw, '%H:%M').time()
        end_time = datetime.fromisoformat(end_time_raw).time() if 'T' in end_time_raw else datetime.strptime(end_time_raw, '%H:%M').time()

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

        if 'delete' in request.POST:
            meeting.delete()
        else:
            meeting.save()

        return redirect('meeting_minutes:meeting_minutes_homepage')

    return render(request, 'meeting_minutes_edit.html', {'meeting': meeting})