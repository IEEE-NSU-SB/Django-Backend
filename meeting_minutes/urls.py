from django.urls import path 
from . import views  

app_name = 'meeting_minutes'

##defining the urls to work with

urlpatterns = [
    
    #meeting_minutes_homepage
    path('',views.meeting_minutes_homepage, name='meeting_minutes_homepage'),
    # Create a new meeting
    path('create/', views.meeting_minutes_create, name="meeting_minutes_create"),

    # Edit an existing meeting
    path('edit/<int:pk>/', views.meeting_minutes_edit, name="meeting_minutes_edit"), # needs pk
    path('meeting-minutes/<int:pk>/pdf/', views.download_meeting_pdf, name='download_meeting_pdf'),
]              
    
