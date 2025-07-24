from datetime import datetime
import logging
import traceback
from rest_framework.response import Response
from rest_framework.views import APIView

from central_branch.renderData import Branch
from insb_port import settings
from main_website.v1.serializers import *
from port.renderData import HandleVolunteerAwards, PortData
from system_administration.models import system
from system_administration.system_error_handling import ErrorHandling
from ..models import News, Blog
from pytz import timezone as tz
from ..renderData import HomepageItems

logger=logging.getLogger(__name__)

class HomepageApiView(APIView):

    def get(self, request, *args, **kwargs):
        try:
            banner_items = HomepageItems.getHomepageBannerItems()
            banner_with_stat = str(HomepageItems.getBannerPictureWithStat())
            HomepageItems.get_ip_address(request)

            all_thoughts = Branch.get_all_homepage_thoughts()
            recent_news = News.objects.order_by('-news_date')[:6]
            recent_blogs = Blog.objects.filter(publish_blog=True).order_by('-date')[:6]
            featured_events = ApiRenderData.load_featured_events(sc_ag_primary=1)
            print(featured_events)

            current_panel_pk = PortData.get_current_panel()
            awards_of_current_panel = HandleVolunteerAwards.load_awards_for_panels(
                request=request, panel_pk=current_panel_pk
            )

            countdown = system.objects.first()
            if countdown and countdown.count_down is not None:
                local_timezone = tz('Asia/Dhaka')
                start_time = countdown.count_down.astimezone(local_timezone)
                start_time = start_time.replace(tzinfo=None)
            else:
                start_time = None

            button_enabled = request.user.is_superuser or request.user.is_staff

            response_data = {
                "banner_item": HomePageTopBannerSerializer(banner_items, many=True).data,
                "banner_pic_with_stat": banner_with_stat,
                "featured_events": FeaturedEventSerializer(featured_events, many=True).data,
                "media_url": settings.MEDIA_URL,
                'stats': {
                    "sc_ag_count": Chapters_Society_and_Affinity_Groups.objects.count() - 1,
                    "all_member_count": HomepageItems.getAllIEEEMemberCount(),
                    "event_count": HomepageItems.getEventCount(),
                    "achievement_count": HomepageItems.getAchievementCount()
                    },
                "recent_news": NewsSerializer(recent_news, many=True).data,
                "recent_blogs": BlogSerializer(recent_blogs, many=True).data,
                # "branch_teams": TeamsSerializer(PortData.get_teams_of_sc_ag_with_id(request=request, sc_ag_primary=1), many=True),
                "all_thoughts": ThoughtSerializer(all_thoughts, many=True).data,
                "awards": AwardSerializer(awards_of_current_panel, many=True).data,
                "start_time": start_time,
                "button_enabled": button_enabled
            }

            return Response(response_data)
        except Exception as e:
            logger.error("An error occurred at {datetime}".format(datetime=datetime.now()), exc_info=True)
            ErrorHandling.saveSystemErrors(error_name=e,error_traceback=traceback.format_exc())
            return Response({'error':'Something went wrong!'})