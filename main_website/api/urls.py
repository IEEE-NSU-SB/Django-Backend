
from django.urls import path
from .views import *


app_name='main_website.api'

urlpatterns = [
    path('get_achievements/', AchievementListView.as_view(), name='achievements_list'),
    path('get_sc_ag_stats/', ScAgStats.as_view(), name='sc_ag_stats'),
    path('get_blogs/landing/', BlogsListLandingView.as_view(), name='blogs_list_landing'),
    path('get_blogs/', BlogsListView.as_view(), name='blogs_list'),
    path('get_volunteer_awards/', VolunteerAwardsListView.as_view(), name='volunteer_awards_list'),
]
