
from central_events.models import Events, SuperEvents
from main_website.renderData import HomepageItems
from port.models import Panels, VolunteerAwards
from port.renderData import PortData
from users.models import VolunteerAwardRecievers
from .serializers import *
from main_website.models import *
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status

class AchievementListView(ListAPIView):
    queryset = Achievements.objects.all().order_by('-award_winning_datefield__year','-award_winning_datefield__month')
    serializer_class = AchievementSerializer

class AchievementListLandingView(ListAPIView):
    queryset = Achievements.objects.all().order_by('-award_winning_datefield__year','-award_winning_datefield__month')[:6]
    serializer_class = AchievementSerializer

class ScAgStats(APIView):

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

        return Response(data)
    
class BlogsListLandingView(ListAPIView):
    queryset = Blog.objects.filter(publish_blog=True).order_by('-date')[:6]
    serializer_class = BlogListSerializer
    
class BlogsView(ListAPIView):

    def get(self, request):
        queryset = Blog.objects.filter(publish_blog=True).order_by('-date')
        serializer = BlogListSerializer(queryset, many=True, context={'request':request})
        return Response(serializer.data)
    
    @csrf_exempt
    def post(self, request):
        serializer = BlogCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message':'Blog submitted successfully!'}, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)  # Debug
        return Response({'message':'An error has occured!'}, status=status.HTTP_400_BAD_REQUEST)

class VolunteerAwardsListView(APIView):

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

        return Response(json_data)

class ToolkitListView(ListAPIView):

    queryset = Toolkit.objects.all().order_by('pk')
    serializer_class = ToolkitSerializer

class FeaturedEventsListView(APIView):

    def get(self, request, sc_ag_primary):
    
        # sc_ag_primary = self.kwargs.get('sc_ag_primary')  # coming from URL kwargs
        # or use: self.request.query_params.get('sc_ag_primary') if it comes from query params

        organiser = Chapters_Society_and_Affinity_Groups.objects.get(primary=sc_ag_primary)

        events_to_view = []
        
        flagship_events = FeaturedEventSerialiser(Events.objects.filter(
            event_organiser=organiser,
            flagship_event=True,
            publish_in_main_web=True
        ).order_by('-start_date', '-event_date'), many=True, context={'request':request}).data

        featured_events = FeaturedEventSerialiser(Events.objects.filter(
            event_organiser=organiser,
            is_featured=True,
            publish_in_main_web=True
        ).order_by('-start_date', '-event_date'), many=True, context={'request':request}).data

        # Combine while removing duplicates by unique ID
        seen_ids = set()

        for event in flagship_events + featured_events:
            event_id = event.get('id')
            if event_id not in seen_ids:
                events_to_view.append(event)
                seen_ids.add(event_id)

        return Response(events_to_view)
    
# class MegaEventsListLandingView(ListAPIView):

#     queryset = SuperEvents.objects.filter(publish_mega_event = True).order_by('-start_date')

class HeroSectionLandingView(APIView):

    def get(self, request):
        
        media_type = MediaToggle.objects.first()
        media_data = HomePageTopBannerSerializer(HomePageTopBanner.objects.filter(media_type=media_type.media_type), context={'media_type': media_type.media_type, 'request': request}, many=True).data

        data = {
            'type': media_type.media_type,
            'media': media_data
        }

        return Response(data)
    
class SBNewsListView(ListAPIView):

    queryset = News.objects.all().order_by('-news_date')
    serializer_class = SBNewsSerializer

class ResearchPapersListView(ListAPIView):

    queryset = Research_Papers.objects.filter(publish_research=True).order_by('-publish_date')
    serializer_class = ResearchPaperSerializer

class AllMembersListView(ListAPIView):

    queryset = Members.objects.filter().all().order_by('position__rank')
    serializer_class = MemberSerializer