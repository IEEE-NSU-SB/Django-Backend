
from django.urls import path
from .views import *


app_name='main_website.api'

urlpatterns = [
    path("achievements/", AchievementListView.as_view(), name="achievements_list"),
]
