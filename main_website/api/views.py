
from django.views import View
from .serializers import *
from main_website.models import *
from rest_framework.generics import ListAPIView

class AchievementListView(ListAPIView):
    queryset = Achievements.objects.all().order_by("-award_winning_year")
    serializer_class = AchievementSerializer