
from django.http import JsonResponse
from django.views import View

from main_website.renderData import HomepageItems
from port.models import Panels, VolunteerAwards
from port.renderData import PortData
from users.models import VolunteerAwardRecievers
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
    
class BlogsListLandingView(ListAPIView):
    queryset = Blog.objects.filter(publish_blog=True).order_by('-date')[:6]
    serializer_class = BlogSerializer
    
class BlogsListView(ListAPIView):
    queryset = Blog.objects.filter(publish_blog=True).order_by('-date')
    serializer_class = BlogSerializer

class VolunteerAwardsListView(View):

    def get(self, request):
        top_5_performers = HomepageItems.get_top_5_performers()
        top_5_teams = HomepageItems.get_top_5_teams()

        current_panel_pk=PortData.get_current_panel()
        all_awards = VolunteerAwards.objects.filter(panel=Panels.objects.get(pk=current_panel_pk))

        top_performers_serializer = TopPerformerSerializer(top_5_performers, many=True, context={'request': request}).data
        top_teams_serializer = TopTeamSerializer(top_5_teams, many=True, context={'request': request}).data

        if top_performers_serializer:
            for i, item in enumerate(top_performers_serializer, start=1):
                item['rank'] = i

        if top_teams_serializer:
            for i, item in enumerate(top_teams_serializer, start=1):
                item['rank'] = i

        json_data = [
            {
                'id': 1,
                'label': "Top 5 Performers",
                'people': top_performers_serializer
            },
            {
                'id': 2,
                'label': "Top 5 Teams",
                'people': top_teams_serializer
            }
        ]

        id = 3
        for award in all_awards:
            awards_winners = VolunteerAwardRecievers.objects.filter(award=VolunteerAwards.objects.get(pk=award.id))
            json_data.append(
                {
                    'id': id,
                    'label': award.volunteer_award_name,
                    'people': VolunteerAwardRecieversSerializer(awards_winners, many=True, context={'request': request}).data
                }
            )
            id += 1

        return JsonResponse(json_data, safe=False)

class ToolkitListView(ListAPIView):

    queryset = Toolkit.objects.all().order_by('pk')
    serializer_class = ToolkitSerializer
    
class ContactInfoView(ListAPIView):
    
    serializer_class = ContactInfoSerializer
    
    def get_queryset(self):
        first_contact = Contact_Info.objects.first()
        return [first_contact] if first_contact else []
