from django.urls import path,include
from . import views
from central_branch.views import task_edit,add_task,create_task,upload_task,task_home,forward_to_incharges
from meeting_minutes.views import meeting_minutes_homepage, meeting_minutes_create, meeting_minutes_edit


app_name='public_relation_team'

urlpatterns = [
    path('',views.team_home_page,name='team_homepage'),
    #Event control page 
    path('event_control/',views.event_control,name="event_control"),
    #Event Creation Form page 1
    path('create_event/page-1',views.event_creation_form_page1,name='event_creation_form1'),
    #Event Creation Form Page 2
    path("create_event/<int:event_id>/page-2", views.event_creation_form_page2, name="event_creation_form2"),
    #Event creation page 3
    path("create_event/<int:event_id>/page-3", views.event_creation_form_page3, name="event_creation_form3"),
    #Super Event Creation Form
    path('create_super_event/',views.super_event_creation,name="super_event_creation"),
    #Manage Event page
    path('manage_event/',views.manage_event,name="manage_event"),
    #Event Dashboard
    path('event_dashboard/<int:event_id>',views.event_dashboard,name='event_dashboard'),
    #Manage Team
    path('manage_team/',views.manage_team,name="manage_team"),
    #Manage website Homepage
    path('manage_website/',views.manageWebsiteHome,name="manage_website_home"),

    #Task
    path('create_task/<int:team_primary>/',create_task,name="create_task_team"),
    path('task_home/<int:team_primary>/',task_home,name="task_home_team"),
    path('task/<int:task_id>/<int:team_primary>/',task_edit,name="task_edit_team"),
    path('task/<int:task_id>/upload_task/<int:team_primary>/',upload_task,name="upload_task_team"),
    path('task/<int:task_id>/forward_to_incharges/<int:team_primary>/',forward_to_incharges,name="forward_to_incharges"),
    path('task/<int:task_id>/add_task/<int:team_primary>/<int:by_coordinators>/',add_task,name="add_task_team"),

    # Meeting Minutes Hompage
    path('meeting_minutes/<int:team_primary>/', meeting_minutes_homepage, name='meeting_minutes_homepage_team'),
    # Create a new meeting
    path('meeting_minutes/<int:team_primary>/create/', meeting_minutes_create, name="meeting_minutes_create_team"),
    # Edit an existing meeting
    path('meeting_minutes/<int:team_primary>/edit/<int:pk>/', meeting_minutes_edit, name="meeting_minutes_edit_team"),
]
