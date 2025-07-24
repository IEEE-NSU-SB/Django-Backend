import os
from rest_framework import serializers

from main_website.renderData import HomepageItems
from ..models import Blog, HomePageTopBanner, BannerPictureWithStat, News, HomePage_Thoughts
from central_events.models import Events
from port.models import Chapters_Society_and_Affinity_Groups, Teams, VolunteerAwards

class SafeResizedImageField(serializers.ImageField):

    def to_representation(self, value):
        try:
            if value and os.path.exists(value.path):
                return super().to_representation(value)
        except (ValueError, AttributeError, FileNotFoundError):
            pass
        return None  # or a default image URL
    
class RawResizedImagePathField(serializers.Field):
    def to_representation(self, value):
        # value is a FieldFile or string (the stored path)
        if not value:
            return None
        # Return the stored file path (string), even if file missing
        # If it's a FieldFile, str(value) gives the path relative to MEDIA_ROOT
        return str(value)
        
class HomePageTopBannerSerializer(serializers.ModelSerializer):
    banner_picture = RawResizedImagePathField()

    class Meta:
        model = HomePageTopBanner
        fields = ['banner_picture']

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = '__all__'

class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = '__all__'

class TeamsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teams
        fields = '__all__'

class FeaturedEventSerializer(serializers.ModelSerializer):
    banner_image = serializers.SerializerMethodField()

    class Meta:
        model = Events
        fields = ['id', 'event_name', 'start_date', 'event_date', 'banner_image']

    def get_banner_image(self, obj):
        return RawResizedImagePathField().to_representation(HomepageItems.load_event_banner_image(event_id=obj.pk))

class AwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = VolunteerAwards
        fields = '__all__'

class ThoughtSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomePage_Thoughts
        fields = '__all__'

class ApiRenderData:
    def load_featured_events(sc_ag_primary):

        '''This function loads 6 events where first 2 are flasghsip and rest featured. If not available then 
            they would be latest event'''
        
        #getting all the flagship, featured and latest events
        flagship_events = Events.objects.filter(event_organiser=Chapters_Society_and_Affinity_Groups.objects.get(primary=sc_ag_primary),flagship_event =True , publish_in_main_web = True).order_by('-start_date','-event_date')
        featured_events=Events.objects.filter(event_organiser=Chapters_Society_and_Affinity_Groups.objects.get(primary=sc_ag_primary),is_featured=True,publish_in_main_web = True).order_by('-start_date','-event_date')
        latest_events = Events.objects.filter(event_organiser=Chapters_Society_and_Affinity_Groups.objects.get(primary=sc_ag_primary),publish_in_main_web = True).order_by('-start_date','-event_date')
        # Initialize lists and set to store the final events and unique event IDs
        final_events = []
        unique_event_ids = set()

        # Combine the event logic as before
        def add_events(queryset, max_count):
            nonlocal final_events, unique_event_ids
            for event in queryset:
                if event.id not in unique_event_ids:
                    final_events.append(event)
                    unique_event_ids.add(event.id)
                if len(final_events) >= max_count:
                    break

        add_events(flagship_events, 2)
        add_events(featured_events, 6)
        add_events(latest_events, 6)
     
        return final_events