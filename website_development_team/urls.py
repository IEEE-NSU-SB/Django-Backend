from django.urls import path,include
from . import views
from central_branch.views import task_edit,add_task,create_task,upload_task,task_home,forward_to_incharges
from meeting_minutes.views import meeting_minutes_homepage, meeting_minutes_create, meeting_minutes_edit

app_name="website_development_team"

urlpatterns = [
    path('',views.team_homepage,name="team_homepage"),
    #Manage Team
    path('manage_team/',views.manage_team,name="manage_team"),
    
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
