
from django.http import JsonResponse
from django.views import View

from main_website.renderData import HomepageItems
from .serializers import *
from main_website.models import *
from rest_framework.generics import ListAPIView
import json

class AchievementListView(ListAPIView):
    queryset = Achievements.objects.all().order_by('-award_winning_datefield__year','-award_winning_datefield__month')
    serializer_class = AchievementSerializer

class ScAgStats(View):

    def get(self, request):
        data = {
            'stats' : [
                {
                    'value': 4,
                    'label': 'CHAPTER & AG'
                },
                {
                    'value': HomepageItems.getAllIEEEMemberCount(),
                    'label': 'MEMBERS'
                },
                {
                    'value': HomepageItems.getEventCount(),
                    'label': 'EVENTS'
                },
                {
                    'value': HomepageItems.getAchievementCount(),
                    'label': 'ACHIEVEMENTS'
                },
            ]
        }

        return JsonResponse(data)
    
class BlogsListView(ListAPIView):
    queryset = Blog.objects.filter(publish_blog=True).order_by('-date')[:6]
    serializer_class = BlogSerializer