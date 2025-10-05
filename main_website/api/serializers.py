
from rest_framework import serializers
from main_website.models import *
from port.models import Teams
from users.models import VolunteerAwardRecievers

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
    
class BlogSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source='blog_banner_picture')
    author = serializers.CharField(source='writer_name')
    category = serializers.SerializerMethodField()
    description = serializers.CharField(source='short_description')

    class Meta:
        model = Blog
        fields = ['id', 'image', 'date', 'author', 'category', 'title', 'description']

    def get_category(self, obj):
        return obj.category.blog_category if obj.category else ''
    
class TopPerformerSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source='ieee_id')
    img = serializers.ImageField(source='user_profile_picture', use_url=True)
    team = serializers.CharField(source='team.team_name')
    rank = serializers.SerializerMethodField()

    class Meta:
        model = Members
        fields = ['id', 'name', 'team','rank', 'img']

    def get_rank(self, obj):
        return 1

class TopTeamSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source='primary')
    img = serializers.ImageField(source='team_picture', use_url=True)
    name = serializers.CharField(source='team_name')
    rank = serializers.SerializerMethodField()

    class Meta:
        model = Teams
        fields = ['id', 'name','rank', 'img']
    
    def to_representation(self, instance):
        """Override default output to make null -> 'null' (string)."""
        data = super().to_representation(instance)
        if data.get('img') is None:
            data['img'] = 'null'  # turn None into a string
        return data

    def get_rank(self, obj):
        return 1
    
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