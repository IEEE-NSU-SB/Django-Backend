
from datetime import datetime
import re
from rest_framework import serializers
from central_events.models import Events, InterBranchCollaborations, IntraBranchCollaborations, SuperEvents
from graphics_team.models import Graphics_Banner_Image
from main_website.models import *
from media_team.models import Media_Images
from port.models import Panels, Teams
from users.models import Panel_Members, VolunteerAwardRecievers
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
    branch_or_society = serializers.SlugRelatedField(
        queryset=Chapters_Society_and_Affinity_Groups.objects.only('id', 'primary'),
        slug_field='primary',   # frontend sends primary, not ID
        required=False,
        allow_null=True
    )

    class Meta:
        model = Blog
        exclude = ['is_requested', 'publish_blog']

    
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
    name = serializers.CharField(source='event_name')
    description = serializers.CharField(source='event_description')
    date = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Events
        fields= ['id', 'name', 'image', 'description', 'date', 'category']

    def get_image(self, obj):

        image = Graphics_Banner_Image.objects.get(event_id = obj.id).selected_image

        request = self.context.get('request')
        if image and hasattr(image, 'url'):
            return str(request.build_absolute_uri(image.url))
        else:
            return ''
        
    def get_category(self, obj):
        categories = obj.event_type.all()

        data = ''
        for cat in categories:
            data += cat.event_category

        return data
    
    def get_date(self, obj):
        return obj.event_date if obj.event_date and obj.start_date == None else obj.start_date

class MegaEventSerializer(serializers.ModelSerializer):

    name = serializers.CharField(source='super_event_name')
    description = serializers.CharField(source='super_event_description')
    image = serializers.ImageField(source='banner_image')

    class Meta:
        model = SuperEvents
        fields = ['id', 'name', 'description', 'image']
        
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
    
class MemberSerializer(serializers.ModelSerializer):

    ieeeId = serializers.IntegerField(source='ieee_id')
    nsuId = serializers.IntegerField(source='nsu_id')
    ieeeEmail = serializers.CharField(source='email_ieee')
    nsuEmail = serializers.CharField(source='email_nsu')
    bloodGroup = serializers.CharField(source='blood_group')

    class Meta:
        model = Members
        fields = ['ieeeId', 'nsuId', 'name', 'ieeeEmail', 'nsuEmail', 'bloodGroup']

class SCAGSerializer(serializers.ModelSerializer):

    name = serializers.CharField(source='short_form_2')
    pageTitle = serializers.CharField(source='page_title')
    pageSubtitle = serializers.CharField(source='secondary_paragraph')
    primaryColor = serializers.CharField(source='primary_color_code')
    missionVisionColor = serializers.CharField(source='mission_vision_color_code')
    secondaryColor = serializers.CharField(source='secondary_color_code')
    textColor = serializers.CharField(source='text_color_code')
    about = serializers.CharField(source='about_description')
    parallax = serializers.ImageField(source='background_image')
    mission = serializers.CharField(source='mission_description')
    missionImage = serializers.ImageField(source='mission_picture')
    vision = serializers.CharField(source='vision_description')
    visionImage = serializers.ImageField(source='vision_picture')
    question = serializers.SerializerMethodField()
    fb = serializers.CharField(source='facebook_link')

    class Meta:
        model = Chapters_Society_and_Affinity_Groups
        fields = ['name', 'pageTitle', 'pageSubtitle', 'primaryColor', 'secondaryColor', 'missionVisionColor', 'textColor', 'logo', 'about', 'parallax', 'mission', 'missionImage', 'vision', 'visionImage', 'question', 'email', 'fb']

    def get_question(self, obj):
        data = {
            '1': obj.what_is_this_description,
            '2': obj.why_join_it,
            '3': obj.what_activites_it_has,
            '4': obj.how_to_join
        }
        return data

class PanelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Panels
        fields = ['year']

class PanelMembersSerializer(serializers.ModelSerializer):
    # position = serializers.StringRelatedField()
    # position_of = serializers.CharField(source='position.role_of.short_form')

    class Meta:
        model = Panel_Members
        fields = ['id', 'name', 'position', 'position_of', 'image', 'linkedin', 'email']


    def to_representation(self, obj):
        request = self.context.get('request') 

        def build_full_url(image_field):
                if image_field and hasattr(image_field, 'url'):
                    if request is not None:
                        return request.build_absolute_uri(image_field.url)
                    return image_field.url  # fallback (relative URL)
                return None
        
        data = {
            'position': str(obj.position) if obj.position else None,
            'position_of': getattr(obj.position.role_of, 'short_form', None) if obj.position else None,
        }

        if obj.member:
            source = obj.member
            data.update({
                'id': getattr(source, 'ieee_id', None),
                'name': getattr(source, 'name', None),
                'image': build_full_url(getattr(source, 'user_profile_picture', None)),
                'facebook': getattr(source, 'facebook_url', None),
                'linkedin': getattr(source, 'linkedin_url', None),
                'email': getattr(source, 'email_nsu', None),
            })
        elif obj.ex_member:
            source = obj.ex_member
            data.update({
                'id': None,
                'name': getattr(source, 'name', None),
                'image': build_full_url(getattr(source, 'picture', None)),
                'linkedin': getattr(source, 'linkedin_link', None),
                'facebook': getattr(source, 'facebook_link', None),
                'email': getattr(source, 'email', None),
            })

        return data
    
class EventSerializer(serializers.ModelSerializer):

    title = serializers.CharField(source='event_name')
    category = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    organizer = serializers.StringRelatedField(source='event_organiser')
    collaboration = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    registration_fee_amount = serializers.SerializerMethodField()
    register_link = serializers.URLField(source='form_link')
    read_more_link = serializers.URLField(source='more_info_link')
    description = serializers.CharField(source='event_description')
    images = serializers.SerializerMethodField()

    class Meta:
        model = Events
        fields= ['id', 'title', 'category', 'image', 'organizer', 'collaboration', 'start_date', 'end_date', 'registration_fee_amount', 'register_link', 'read_more_link', 'description', 'images']

    def get_image(self, obj):

        image = Graphics_Banner_Image.objects.get(event_id = obj.id).selected_image

        request = self.context.get('request')
        if image and hasattr(image, 'url'):
            return str(request.build_absolute_uri(image.url))
        else:
            return ''
        
    def get_category(self, obj):
        categories = obj.event_type.all()

        data = ''
        for cat in categories:
            data += cat.event_category

        return data
    
    def get_registration_fee_amount(self, obj):
        if obj.registration_fee:
            return obj.registration_fee_amount
        else:
            return 'Free'

    def get_start_date(self, obj):
        return obj.event_date if obj.event_date and obj.start_date == None else obj.start_date
    
    def get_collaboration(self, obj):
        get_inter_branch_collab=InterBranchCollaborations.objects.filter(event_id=obj.pk)
        get_intra_branch_collab=IntraBranchCollaborations.objects.filter(event_id=obj.pk).first()
        return 'Google Developers Group Dhaka'
    
    def get_images(self, obj):
        request = self.context.get('request')
        images = Media_Images.objects.filter(event_id=obj.pk)
        selected_images = []

        for image in images:
            selected_images.append(str(request.build_absolute_uri(image.selected_images.url)))

        return selected_images