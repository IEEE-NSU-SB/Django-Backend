
from datetime import datetime
import re
from rest_framework import serializers
from central_events.models import Events
from graphics_team.models import Graphics_Banner_Image
from main_website.models import *
from port.models import Teams
from users.models import VolunteerAwardRecievers
from django.utils.html import strip_tags
from datetime import date

class AchievementSerializer(serializers.ModelSerializer):
    year = serializers.SerializerMethodField()
    image = serializers.ImageField(source='award_picture', use_url=True)
    title = serializers.CharField(source='award_name')
    description = serializers.CharField(source="award_description")
    winner = serializers.CharField(source='award_of')
    primaryColor = serializers.CharField(source='award_of.primary_color_code')

    class Meta:
        model = Achievements
        fields = ["year", "image", "title", 'winner', 'primaryColor', "description"]

    def get_year(self, obj):
        return str(obj.award_winning_year)
    
class BlogListSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source='blog_banner_picture')
    author = serializers.CharField(source='writer_name')
    category = serializers.SerializerMethodField()
    description = serializers.CharField(source='short_description')

    class Meta:
        model = Blog
        fields = ['id', 'image', 'date', 'author', 'category', 'title', 'description']

    def get_category(self, obj):
        return obj.category.blog_category if obj.category else ''

class BlogCreateSerializer(serializers.ModelSerializer):

    date = serializers.DateField(default=date.today)  # auto-fill today if not provided

    class Meta:
        model = Blog
        exclude = ['is_requested', 'publish_blog']

    # def validate_branch_or_society(self, value):
    #     """
    #     Convert the frontend value to the actual ForeignKey instance.
    #     """
    #     try:
    #         # Replace 'code' with the actual field in your Chapters_Society_and_Affinity_Groups model
    #         return Chapters_Society_and_Affinity_Groups.objects.get(primary=value).pk
    #     except Chapters_Society_and_Affinity_Groups.DoesNotExist:
    #         raise serializers.ValidationError(f"No branch/society found with value '{value}'")
    
class TopPerformerSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source='ieee_id')
    img = serializers.ImageField(source='user_profile_picture', use_url=True)
    team = serializers.SerializerMethodField()

    class Meta:
        model = Members
        fields = ['id', 'name', 'team','img']

    def get_team(self, obj):
        return obj.team.team_name if obj.team else ''

class TopTeamSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source='primary')
    img = serializers.ImageField(source='team_picture', use_url=True)
    name = serializers.CharField(source='team_name')

    class Meta:
        model = Teams
        fields = ['id', 'name', 'img']
    
    def to_representation(self, instance):
        """Override default output to make null -> 'null' (string)."""
        data = super().to_representation(instance)
        if data.get('img') is None:
            data['img'] = 'null'  # turn None into a string
        return data
    
class VolunteerAwardRecieversSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source='award_reciever.ieee_id')
    img = serializers.ImageField(source='award_reciever.user_profile_picture', use_url=True)
    name = serializers.CharField(source='award_reciever.name')
    team = serializers.CharField(source='award_reciever.team')

    class Meta:
        model = VolunteerAwardRecievers
        fields = ['id', 'name', 'team', 'img']

    def to_representation(self, instance):
        """Override default output to make null -> 'null' (string)."""
        data = super().to_representation(instance)
        if data.get('img') is None:
            data['img'] = 'null'  # turn None into a string
        return data
    
class ToolkitSerializer(serializers.ModelSerializer):

    img = serializers.ImageField(source='picture')
    colors = serializers.SerializerMethodField()

    class Meta:
        model = Toolkit
        fields = ['title', 'img', 'colors']

    def get_colors(self, obj):
        return re.split(r'[\r\n]+', strip_tags(str(obj.color_codes)))
    
class FeaturedEventSerialiser(serializers.ModelSerializer):

    image = serializers.SerializerMethodField()
    alt = serializers.CharField(source='event_name')

    class Meta:
        model = Events
        fields= ['id', 'image', 'alt']

    def get_image(self, obj):

        image = Graphics_Banner_Image.objects.get(event_id = obj.id).selected_image

        request = self.context.get('request')
        if image and hasattr(image, 'url'):
            return str(request.build_absolute_uri(image.url))
        else:
            return ''
        
# class MegaEventSerialiser(serializers.ModelSerializer):
    
class HomePageTopBannerSerializer(serializers.ModelSerializer):

    banner_image = serializers.ImageField(source='banner_picture')
    alt = serializers.SerializerMethodField()
    firstText = serializers.CharField(source='first_layer_text')
    secondText = serializers.CharField(source='first_layer_text_colored')
    description = serializers.CharField(source='third_layer_text')
    buttonText = serializers.CharField(source='button_text')
    buttonLink = serializers.CharField(source='button_url')
    link = serializers.FileField(source='video')

    class Meta:
        model = HomePageTopBanner
        fields = [
            'banner_image', 'alt', 'firstText', 'secondText', 'description', 'buttonText', 'buttonLink', 'link'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        media_type = self.context.get('media_type')

        if media_type == 'image':
            allowed = {'banner_image', 'alt', 'firstText', 'secondText', 'description', 'buttonText', 'buttonLink'}
        elif media_type == 'video':
            allowed = {'link'}
        else:
            allowed = set(self.fields.keys())  # default: all fields

        # Remove any fields not in allowed list
        for field_name in list(self.fields.keys()):
            if field_name not in allowed:
                self.fields.pop(field_name)
    
    def get_alt(self, obj):
        return f'{obj.first_layer_text} {obj.first_layer_text_colored}'

class SBNewsSerializer(serializers.ModelSerializer):

    image = serializers.ImageField(source='news_picture')
    title = serializers.CharField(source='news_title')
    description = serializers.CharField(source='news_subtitle')

    class Meta:
        model = News
        fields = ['id', 'image', 'title', 'description']

class ResearchPaperSerializer(serializers.ModelSerializer):

    authors = serializers.SerializerMethodField()
    link = serializers.URLField(source='publication_link')

    class Meta:
        model = Research_Papers
        fields = ['id', 'title', 'authors', 'link']

    def get_authors(self, obj):
        author_names = strip_tags(obj.author_names).replace('&nbsp;', '').split(',')
        return author_names