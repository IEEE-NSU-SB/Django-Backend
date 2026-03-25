
import json
import requests
from central_events.models import Events, SuperEvents
from chapters_and_affinity_group.models import SC_AG_Members
from insb_port import settings
from main_website.renderData import HomepageItems
from port.models import Panels, Roles_and_Position, VolunteerAwards
from port.renderData import PortData
from recruitment.models import recruited_members, recruitment_session
from system_administration.models import Project_Developers, Project_leads, system
from system_administration.render_access import Access_Render
from users.models import Panel_Members, VolunteerAwardRecievers
from .serializers import *
from main_website.models import *
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from users.renderData import getTypeOfEventStats, getEventNumberStat
from django.utils import timezone

class SwitchesAPI(APIView):

    def get(self, request):
        get_system=system.objects.first()

        if request.user.is_authenticated:

            if(Access_Render.system_administrator_superuser_access(username=request.user.username) or Access_Render.system_administrator_staffuser_access(username=request.user.username)
                or Access_Render.eb_access(username=request.user.username) or Access_Render.belongs_to_sc_ag_panels(username=request.user.username)):
                
                
                return Response({
                    "config": {
                        'main_website_under_maintenance': False,
                    },
                })
            else:
                return Response({
                    "config": {
                        'main_website_under_maintenance': get_system.main_website_under_maintenance,
                    },
                })
        else:
                return Response({
                    "config": {
                        'main_website_under_maintenance': get_system.main_website_under_maintenance,
                    },
                })

class AchievementListView(ListAPIView):
    serializer_class = AchievementSerializer

    def get_queryset(self):
        sc_ag_primary = self.kwargs.get('sc_ag_primary')
        
        if sc_ag_primary:
            return Achievements.objects.filter(award_of=Chapters_Society_and_Affinity_Groups.objects.get(primary=sc_ag_primary)).order_by('-award_winning_datefield__year','-award_winning_datefield__month')
        else:
            return Achievements.objects.all().order_by('-award_winning_datefield__year','-award_winning_datefield__month')

class AchievementListLandingView(ListAPIView):
    serializer_class = AchievementSerializer

    def get_queryset(self):
        sc_ag_primary = self.kwargs.get('sc_ag_primary')
        
        if sc_ag_primary:
            return Achievements.objects.filter(award_of=Chapters_Society_and_Affinity_Groups.objects.get(primary=sc_ag_primary)).order_by('-award_winning_datefield__year','-award_winning_datefield__month')[:6]
        else:
            return Achievements.objects.all().order_by('-award_winning_datefield__year','-award_winning_datefield__month')[:6]

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
    
class EventsStats(APIView):

    def get(self, request):

        get_event_stat=getTypeOfEventStats(request,1)
        event_stat=[]
        # prepare data from the tuple
        categories, count, percentage_mapping = get_event_stat
        for category, count in zip(categories, count):
            event_stat_dict={}
            # get event name
            event_stat_dict['name']=category
            # get event count according to category
            event_stat_dict['value']=count
            # append the dict to list
            event_stat.append(event_stat_dict)

        get_yearly_events=getEventNumberStat(request,1)

        data = {
            'eventCounts': event_stat,
            'yearlyEvents': {
                'years': get_yearly_events[0],
                'count': get_yearly_events[1]
            }
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
    
    @method_decorator(ensure_csrf_cookie)
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
            
            flagship_events = EventListSerialiser(Events.objects.filter(
                event_organiser=organiser,
                flagship_event=True,
                publish_in_main_web=True
            ).order_by('-start_date', '-event_date'), many=True, context={'request':request}).data

            featured_events = EventListSerialiser(Events.objects.filter(
                event_organiser=organiser,
                is_featured=True,
                publish_in_main_web=True
            ).order_by('-start_date', '-event_date'), many=True, context={'request':request}).data

            mega_events = SuperEvents.objects.filter(mega_event_of=organiser, publish_mega_event = True).order_by('-start_date')

        else:
            flagship_events = EventListSerialiser(Events.objects.filter(
                flagship_event=True,
                publish_in_main_web=True
            ).order_by('-start_date', '-event_date'), many=True, context={'request':request}).data

            featured_events = EventListSerialiser(Events.objects.filter(
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

        mega_events_to_view = MegaEventListSerializer(mega_events, many=True, context={'request':request}).data

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
    serializer_class = SBNewsListSerializer

class ResearchPapersListView(ListAPIView):

    queryset = Research_Papers.objects.filter(publish_research=True).order_by('-publish_date')
    serializer_class = ResearchPaperSerializer

class AllMembersListView(ListAPIView):

    queryset = Members.objects.filter().all().order_by('position__rank')
    serializer_class = MembersListSerializer

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
    serializer_class = EventListSerialiser
    pagination_class = EventPagination

class TeamInfoView(APIView):

    def get(self, request, team_primary):
        team_details = Teams.objects.get(primary=team_primary)
        team_serialized = TeamSerializer(team_details, context={'request':request}).data

        team_co_ordinators=[]
        team_incharges=[]
        core_volunteers=[]
        volunteers=[]

        get_team_members=PortData.get_specific_team_members_of_current_panel(request=request,team_primary=team_details.primary)
        if(get_team_members):
            for i in get_team_members:
                if(i.position.is_officer):
                    if(i.position.is_co_ordinator):
                        team_co_ordinators.append(i)
                    else:
                        team_incharges.append(i)
                elif(i.position.is_core_volunteer and i.position.is_volunteer):
                    core_volunteers.append(i)
                elif(i.position.is_volunteer):
                    volunteers.append(i)

        team_co_ordinators_serialized = TeamPanelMembersSerializer(team_co_ordinators, many=True, context={'request': request}).data
        team_incharges_serialized = TeamPanelMembersSerializer(team_incharges, many=True, context={'request': request}).data
        core_volunteers_serialized = TeamPanelMembersSerializer(core_volunteers, many=True, context={'request': request}).data
        volunteers_serialized = TeamPanelMembersSerializer(volunteers, many=True, context={'request': request}).data

        data = {
            'team': team_serialized,
            'subExecutive': team_co_ordinators_serialized,
            'incharge': team_incharges_serialized,
            'coreVolunteers': core_volunteers_serialized,
            'volunteers': volunteers_serialized
        }

        return Response(data)
    
class SCAGPanelExecutives(APIView):

    def get(self, request, sc_ag_primary, panel_year=None):
        #getting the particular society object
        society = Chapters_Society_and_Affinity_Groups.objects.get(primary=sc_ag_primary)

        if panel_year:
            tenure = Panels.objects.get(panel_of = society, year=panel_year)
        else:
            #getting current tenure
            tenure = Panels.objects.get(current = True, panel_of = society)
            pass        
        #getting the faculty
        faculty_advisor = Panel_Members.objects.filter(tenure = tenure, position = Roles_and_Position.objects.get(is_faculty = True,role_of = society,is_sc_ag_eb_member = True))
        faculty_advisor_serialized = PanelMembersSerializer(faculty_advisor, many=True, context={'request': request}).data

        eb_members = []
        roles = Roles_and_Position.objects.filter(is_sc_ag_eb_member = True,role_of = society,is_faculty=False).order_by('rank','role','role_of')
        for role in roles:
            try:
                #getting the member of the particular society whose role matches with the role iteration in the list and is if current panel
                member = Panel_Members.objects.filter(tenure = tenure,position = role)
                eb_members.extend(member)
            except:
                pass
        eb_members_serialized = PanelMembersSerializer(eb_members, many=True, context={'request': request}).data

        data = {
            'advisor': faculty_advisor_serialized,
            'executives': eb_members_serialized
        }

        return Response(data)

class TeamsListView(APIView):

    def get(self, request):
        teams = Teams.objects.filter(is_active=True,team_of=Chapters_Society_and_Affinity_Groups.objects.get(primary=1)).all().order_by('id')
        teams_serializer = TeamListSerializer(teams, many=True).data

        return Response(teams_serializer)

class OfficersListView(ListAPIView):

    serializer_class = PanelMembersSerializer

    def get_queryset(self):

        currentPanel=Panels.objects.get(current=True,panel_of=Chapters_Society_and_Affinity_Groups.objects.get(primary=1))
        
        team_primary = self.kwargs.get('team_primary')
        if team_primary:
            team = Teams.objects.get(primary=team_primary)            
            officers=Panel_Members.objects.filter(tenure=currentPanel, team=team, position__is_officer=True)
        else:
            officers=Panel_Members.objects.filter(tenure=currentPanel, position__is_officer=True)

        return officers
    
class VolunteersListView(ListAPIView):

    serializer_class = PanelMembersSerializer

    def get_queryset(self):
        currentPanel=Panels.objects.get(current=True,panel_of=Chapters_Society_and_Affinity_Groups.objects.get(primary=1))
        
        team_primary = self.kwargs.get('team_primary')
        if team_primary:
            team = Teams.objects.get(primary=team_primary)            
            volunteers=Panel_Members.objects.filter(Q(position__is_volunteer=True) | Q(position__is_core_volunteer=True), tenure=currentPanel, team=team)
        else:
            volunteers=Panel_Members.objects.filter(Q(position__is_volunteer=True) | Q(position__is_core_volunteer=True), tenure=currentPanel)

        return volunteers
    
class SBNewsDetails(APIView):

    def get(self, request, news_id):

        news=News.objects.get(pk=news_id)
        news_serialized = SBNewsSerializer(news, context={'request':request}).data   
        # get recent 3 news
        recent_news=News.objects.all().order_by('-news_date').exclude(pk=news_id)[:3]
        recent_news_serialized = SBNewsSerializer(recent_news, many=True, context={'request':request}).data
        
        # get recent 5 blogs
        recent_blogs=Blog.objects.filter(publish_blog=True).order_by('-date')[:5]
        recent_blogs_serialized = BlogListTitleSerializer(recent_blogs, many=True).data

        data = {
            'recentNews': recent_news_serialized,
            'recentBlogs': recent_blogs_serialized
        }

        news_serialized.update(data)

        return Response(news_serialized)
    
class MegaEventView(APIView):

    def get(self, request, event_id):

        mega_event = SuperEvents.objects.get(id=event_id)
        mega_event_serialized = MegaEventSerializer(mega_event, context={'request':request}).data

        organised_events = Events.objects.filter(super_event_id=mega_event,publish_in_main_web=True).order_by('-start_date','-event_date')
        organised_events_serialized = EventSmallListSerialiser(organised_events, many=True, context={'request':request}).data

        other_mega_events = SuperEvents.objects.filter(publish_mega_event=True).exclude(id=mega_event.id).order_by('-start_date')[:6]
        other_mega_events_serialized = MegaEventListTitleSerializer(other_mega_events, many=True, context={'request':request}).data
        
        data = {
            'organisedEvents': organised_events_serialized,
            'megaEvents': other_mega_events_serialized
        }
        mega_event_serialized.update(data)

        return Response(mega_event_serialized)
    
class MemberProfileView(APIView):

    def get(self, request, ieee_id):

        member_details = Members.objects.get(ieee_id=ieee_id)
        member_details_serialized = MemberSerializer(member_details, context={'request':request}).data

        awards = VolunteerAwardRecievers.objects.filter(award_reciever=member_details)
        awards_serialized = VolunteerAwardTitleSerializer(awards, many=True).data

        branch_current_position_data = {
            'organization': 'IEEE NSU SB',
            'currentPosition': member_details.position.role if member_details.position else 'None',
            'team': member_details.team.team_name if member_details.team else '',
            'tenure': '',
            'current': True
        }

        #get current sc_ag position data for all sc_ag
        sc_ag_position_data = SC_AG_Members.objects.filter(member=ieee_id).order_by('sc_ag__primary')

        #get previous branch position data
        branch_prev_position_data = PortData.get_branch_previous_position_data(ieee_id)
        branch_prev_position_data_serialized = PanelMemberPositionSerializer(branch_prev_position_data, many=True).data
        
        #get previous sc_ag position data for all sc_ag
        sc_ag_previous_position_data=Panel_Members.objects.filter(~Q(tenure__panel_of__primary=1), member=Members.objects.get(ieee_id=ieee_id),tenure__current=False).order_by('-tenure__year')
        # sc_ag_previous_position_data_serialized = PanelMemberPositionSerializer(sc_ag_previous_position_data, many=True).data
        sc_ag_position_data_serialized = []
        for data in sc_ag_position_data:
            if data.position:
                sc_ag_position_data_serialized.append(
                    {
                        'organization': data.sc_ag.short_form,
                        'currentPosition': data.position.role if data.position else 'None',
                        'team': data.team.team_name if data.team else '',
                        'tenure': '',
                        'current': True
                    }
                )

            for prev_data in sc_ag_previous_position_data:
                if prev_data.position.role_of.primary == data.sc_ag.primary:
                    sc_ag_position_data_serialized.append(PanelMemberPositionSerializer(prev_data).data)

        roles = []
        roles.append(branch_current_position_data)
        roles.extend(branch_prev_position_data_serialized)
        roles.extend(sc_ag_position_data_serialized)

        data = {
            'achievements':awards_serialized,
            'roles':roles,
        }
        member_details_serialized.update(data)

        return Response(member_details_serialized)
    
class BlogView(APIView):

    def get(self, request, blog_id):
        blog = Blog.objects.get(pk=blog_id)
           
        blog_serialized = BlogSerializer(blog, context={'request':request}).data
        if blog.branch_or_society == None:
            blog_serialized['publishedFrom'] = 'IEEE NSU Student Branch'
        
        recent_blogs = Blog.objects.filter(publish_blog=True).order_by('-date').exclude(pk=blog_id)[:3]
        recent_blogs_serialized = BlogSmallListSerializer(recent_blogs, many=True, context={'request':request}).data
        recent_news = News.objects.all().order_by('-news_date')[:5]
        recent_news_serialized = SBNewsTitleListSerializer(recent_news, many=True).data

        data = {
            'recentBlogs': recent_blogs_serialized,
            'recentNews': recent_news_serialized
        }
        blog_serialized.update(data)

        return Response(blog_serialized)

class UpcomingEvent(APIView):

    def get(self, request):
        current_datetime = timezone.now()
        upcoming_event = Events.objects.filter(publish_in_main_web = True,start_date__gt=current_datetime).order_by('start_date').first()
        if upcoming_event:
            upcoming_event_serialized = UpcomingEventSerializer(upcoming_event, context={'request':request}).data
            return Response(upcoming_event_serialized)
        else:
            return Response({})

class ExemplaryMembersListView(ListAPIView):

    queryset = ExemplaryMembers.objects.all().order_by('rank')
    serializer_class = ExemplaryMemberSerializer

class FAQView(APIView):

    def get(self, request):
        all_categories = FAQ_Question_Category.objects.all().order_by('id')

        data = {}

        for category in all_categories:
            question_answers_serialized = FAQ_QuestionsSerializer(FAQ_Questions.objects.filter(title=category).order_by('pk'), many=True).data
            data.update({
                category.title: question_answers_serialized
            })

        return Response(data)
    
class GalleryView(APIView):

    def get(self, request):

        all_images=GalleryImages.objects.all().order_by('-pk')
        all_videos=GalleryVideos.objects.all().order_by('-pk')

        all_images_serialized = GalleryImageSerializer(all_images, many=True, context={'request':request}).data
        all_videos_serialized = GalleryVideoSerializer(all_videos, many=True).data

        data = {
            'images': all_images_serialized,
            'videos': all_videos_serialized
        }

        return Response(data)

@method_decorator(ensure_csrf_cookie, name="dispatch")
class SC_AG_FeedBack(APIView):

    def post(self, request, sc_ag_primary=None):

        if sc_ag_primary:
            request.data['society'] = sc_ag_primary
        else:
            request.data['society'] = 1

        serializer = SC_AG_FeedBack_CreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message':'Feedback submitted successfully!'}, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)  # Debug
        return Response({'message':'An error has occured!'}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(ensure_csrf_cookie, name="dispatch")   
class AddResearchPaperView(APIView):

    def post(self, request):
        
        serializer = ResearchPaper_CreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message':'Research Paper submitted successfully!'}, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)  # Debug
        return Response({'message':'An error has occured!'}, status=status.HTTP_400_BAD_REQUEST)

class EventFeedbackView(APIView):

    def get(self, request, event_id):

        event_feedbacks = Event_Feedback.objects.filter(event_id=event_id, approved=True)
        event_feedbacks_serialized = EventFeedbackSerializer(event_feedbacks, many=True).data

        return Response(event_feedbacks_serialized)

    @method_decorator(ensure_csrf_cookie)
    def post(self, request, event_id):
        
        request.data['event_id'] = event_id
        serializer = EventFeedback_CreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message':'Feedback submitted successfully!'}, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)  # Debug
        return Response({'message':'An error has occured!'}, status=status.HTTP_400_BAD_REQUEST)
    
class PortalDevelopersList(APIView):

    def get(self, request):
        
        project_leads=Project_leads.objects.all()
        project_developers=Project_Developers.objects.all().order_by('-reputation_point')

        project_leads_serialized = ProjectLeadsSerializer(project_leads, many=True, context={'request':request}).data
        project_developers_serialized = ProjectDevelopersSerializer(project_developers, many=True, context={'request':request}).data

        data = {
            'project_leads':project_leads_serialized,
            'project_developers':project_developers_serialized
        }

        return Response(data)
    
class MagazinesListView(ListAPIView):

    serializer_class = MagazinesSerializer
    queryset = Magazines.objects.all().order_by('-publish_date')