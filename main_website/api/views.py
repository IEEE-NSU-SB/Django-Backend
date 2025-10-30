
import json
import requests
from central_events.models import Events, SuperEvents
from insb_port import settings
from main_website.renderData import HomepageItems
from port.models import Panels, VolunteerAwards
from port.renderData import PortData
from recruitment.models import recruited_members, recruitment_session
from users.models import Panel_Members, VolunteerAwardRecievers
from .serializers import *
from main_website.models import *
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

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
    
class BlogsView(APIView):

    def get(self, request):
        blogs = Blog.objects.filter(publish_blog=True).order_by('-date')
        serializer = BlogListSerializer(blogs, many=True, context={'request':request})
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

class MegaEvents_FeaturedEventsListView(APIView):

    def get(self, request, sc_ag_primary):
    
        # sc_ag_primary = self.kwargs.get('sc_ag_primary')  # coming from URL kwargs
        # or use: self.request.query_params.get('sc_ag_primary') if it comes from query params

        events_to_view = []

        if sc_ag_primary != 1:
            organiser = Chapters_Society_and_Affinity_Groups.objects.get(primary=sc_ag_primary)
            
            flagship_events = EventSerialiser(Events.objects.filter(
                event_organiser=organiser,
                flagship_event=True,
                publish_in_main_web=True
            ).order_by('-start_date', '-event_date'), many=True, context={'request':request}).data

            featured_events = EventSerialiser(Events.objects.filter(
                event_organiser=organiser,
                is_featured=True,
                publish_in_main_web=True
            ).order_by('-start_date', '-event_date'), many=True, context={'request':request}).data

            mega_events = SuperEvents.objects.filter(mega_event_of=organiser, publish_mega_event = True).order_by('-start_date')

        else:
            flagship_events = EventSerialiser(Events.objects.filter(
                flagship_event=True,
                publish_in_main_web=True
            ).order_by('-start_date', '-event_date'), many=True, context={'request':request}).data

            featured_events = EventSerialiser(Events.objects.filter(
                is_featured=True,
                publish_in_main_web=True
            ).order_by('-start_date', '-event_date'), many=True, context={'request':request}).data

            mega_events = SuperEvents.objects.filter(publish_mega_event = True).order_by('-start_date')

        # Combine while removing duplicates by unique ID
        seen_ids = set()

        for event in flagship_events + featured_events:
            event_id = event.get('id')
            if event_id not in seen_ids:
                events_to_view.append(event)
                seen_ids.add(event_id)

        mega_events_to_view = MegaEventSerializer(mega_events, many=True, context={'request':request}).data

        data = {
            'featuredEvents':events_to_view,
            'megaEvents':mega_events_to_view
        }

        return Response(data)

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

class AllMembersStats(APIView):

    def get(self, request):

        recruitment_stats=[]
        
        for i in recruitment_session.objects.all().order_by('-id')[:5]:
            recruitee_count=recruited_members.objects.filter(session_id=i.id).count()
            recruitment_stats.append({'semester':i.session, 'recruits': recruitee_count})

        data = {
            'recruitment' : reversed(recruitment_stats),
            'genderDistribution' : [
                {'gender':'Male', 'count':Members.objects.filter(gender="Male").count()},
                {'gender':'Female', 'count':Members.objects.filter(gender="Female").count()}
            ]
        }

        return Response(data)

class OnlineNewsListView(APIView):
    
    def get(self, request):
        # apis to get online news
        url_robotics=f'https://newsdata.io/api/1/news?apikey={settings.NEWS_API_KEY}&q=robotics&language=en&category=education,science,technology'
        url_wie_news=f'https://newsdata.io/api/1/news?apikey={settings.NEWS_API_KEY}&q="women%20in%20STEM"&category=technology'
        url_ai_machine_learning=f'https://newsdata.io/api/1/news?apikey={settings.NEWS_API_KEY}&q="artificial%20neural%20network"%20OR%20"deep%20learning"&language=en&category=technology,top '

        # keeping urls as list
        url_list=[url_robotics,url_ai_machine_learning,url_wie_news]
        
        json_datas=[]
        # extracting response from the apis and keeping all the three datas of the api in a list
        for url in url_list:
            response=requests.get(url)
            if(response.status_code==200):
                # if response is okay then load data
                json_datas.append(json.loads(response.text))

        all_online_news=[]
        # extracting article results
        for i in json_datas:
            articles=i.get('results',[])        
            for article in articles:
                # extracting article values
                title=article.get('title',[])
                article_link=article.get('link',[])
                article_description=article.get('description',[])
                article_picture=article.get('image_url',[])
                article_creator=article.get('creator',[]) or []
                article_id=article.get('article_id',[])
                article_publish_date=article.get('pubDate',[])
                # storing all articles as dictionary key value items
                news_item={
                    'id':article_id,
                    'date':article_publish_date,
                    'title':title,
                    'article_link':article_link,
                    'description':article_description,
                    'image':article_picture,
                    'by': article_creator
                }
                # storing all articles in a list
                all_online_news.append(news_item)

        return Response(all_online_news)
    
class SCAGDetails(APIView):

    def get(self, request, sc_ag_primary):
        
        sc_ag = Chapters_Society_and_Affinity_Groups.objects.get(primary=sc_ag_primary)
        serialized = SCAGSerializer(sc_ag, context={'request':request})

        return Response(serialized.data)
    
class PanelsListView(APIView):

    def get(self, request, sc_ag_primary=None):
        if sc_ag_primary:
            panels = Panels.objects.filter(panel_of=Chapters_Society_and_Affinity_Groups.objects.get(primary=sc_ag_primary)).order_by('-current','-year')[1:]
            print(panels.query)
        else:
            panels = Panels.objects.filter(panel_of=Chapters_Society_and_Affinity_Groups.objects.get(primary=1)).order_by('-current','-year')[1:]

        serialized_data = PanelSerializer(panels, many=True).data

        return Response(serialized_data)
    
class PanelExecutives(APIView):

    def get(self, request, panel_year=None):

        # Get all current panels for primary 1–5 in one query

        if panel_year:
            panels = Panels.objects.filter(year=panel_year, panel_of__primary__in=range(1,6))
        else:
            panels = Panels.objects.filter(current=True, panel_of__primary__in=range(1,6))

        # Prefetch members for all panels at once
        all_members = Panel_Members.objects.filter(tenure__in=panels).select_related('position', 'tenure')

        current_panel_branch_counselors = []
        current_panel_mentors = []
        current_panel_excom = []
        current_panel_sc_ag_chairs = []

        for i in all_members:
            if (i.position.role_of.primary==1):
                if(i.position.is_faculty):
                    current_panel_branch_counselors.append(i)
                elif(i.position.is_eb_member):
                    if(i.position.is_mentor):
                        current_panel_mentors.append(i)
                    else:
                        current_panel_excom.append(i)
            elif(i.position.is_sc_ag_eb_member):
                if(i.position.role == 'Chair'):
                    current_panel_sc_ag_chairs.append(i)

        current_panel_faculty_advisors = [
            m for m in all_members
            if m.tenure.panel_of.primary in range(2,6) and m.position.is_sc_ag_eb_member and m.position.is_faculty
        ]
        
        current_panel_branch_counselors_serialized = PanelMembersSerializer(current_panel_branch_counselors, many=True, context={'request': request}).data
        current_panel_faculty_advisors_serialized = PanelMembersSerializer(current_panel_faculty_advisors, many=True, context={'request': request}).data
        current_panel_mentors_serialized = PanelMembersSerializer(current_panel_mentors, many=True, context={'request': request}).data
        current_panel_excom_serialized = PanelMembersSerializer(current_panel_excom, many=True, context={'request': request}).data
        current_panel_sc_ag_chairs_serialized = PanelMembersSerializer(current_panel_sc_ag_chairs, many=True, context={'request': request}).data

        data = {
            'counselors':current_panel_branch_counselors_serialized,
            'sc_ag_faculty_advisors': current_panel_faculty_advisors_serialized,
            'mentors': current_panel_mentors_serialized,
            'excom': current_panel_excom_serialized,
            'sc_ag_chairs': current_panel_sc_ag_chairs_serialized
        }

        return Response(data)
    
class EventView(RetrieveAPIView):

    serializer_class = EventSerializer
    queryset = Events.objects.all()
    
    lookup_field = 'id'              # model field name
    lookup_url_kwarg = 'event_id'    # URL parameter name
    
class ContactInfoView(RetrieveAPIView):
    serializer_class = ContactInfoSerializer

    def get_object(self):
        return Contact_Info.objects.first()
    
class IEEERegion10Details(RetrieveAPIView):

    serializer_class = IEEERegion10Serializer

    def get_object(self):
        return IEEE_Region_10.objects.first()
    
class EventPagination(PageNumberPagination):
    page_size = 20  # Events per page
    # page_size_query_param = 'page_size'  # optional, allows ?page_size=3
    # max_page_size = 50

class EventsListView(ListAPIView):

    queryset = Events.objects.filter(publish_in_main_web= True,).order_by('-start_date','-event_date') 
    serializer_class = EventSerializer
    pagination_class = EventPagination