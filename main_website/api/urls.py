
from django.urls import path
from .views import *


app_name='main_website.api'

urlpatterns = [
    path('get_hero_section_landing/', HeroSectionLandingView.as_view(), name='hero_section_landing'),
    path('get_achievements/', AchievementListView.as_view(), name='achievements_list'),
    path('get_achievements/landing/', AchievementListLandingView.as_view(), name='achievements_list_landing'),
    path('get_sc_ag_stats/', ScAgStats.as_view(), name='sc_ag_stats'),
    path('get_blogs/landing/', BlogsListLandingView.as_view(), name='blogs_list_landing'),
    path('get_blogs/', BlogsView.as_view(), name='blogs_list'),
    path('get_volunteer_awards/', VolunteerAwardsListView.as_view(), name='volunteer_awards_list'),
    path('get_toolkit/', ToolkitListView.as_view(), name='toolkit_list'),
    path('get_mega_featured_events/<int:sc_ag_primary>/', MegaEvents_FeaturedEventsListView.as_view(), name='mega_featured_events_list'),
    path('get_sb_news/', SBNewsListView.as_view(), name='sb_news_list'),
    path('get_online_news/', OnlineNewsListView.as_view(), name='online_news_list'),
    # path('get_mega_events/landing/', MegaEventsListLandingView.as_view(), name='mega_events_list_landing')
    path('get_research_papers/', ResearchPapersListView.as_view(), name='research_papers_list'),
    path('get_all_members/', AllMembersListView.as_view(), name='all_members_list'),
    path('get_all_members_stats/', AllMembersStats.as_view(), name='all_members_stats'),
    path('get_sc_ag_details/<int:sc_ag_primary>/', SCAGDetails.as_view(), name='sc_ag_details'),
]
