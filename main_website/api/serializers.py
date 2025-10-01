
from rest_framework import serializers
from main_website.models import *

class AchievementSerializer(serializers.ModelSerializer):
    year = serializers.SerializerMethodField()
    image = serializers.ImageField(source='award_picture', use_url=True)
    title = serializers.SerializerMethodField()
    description = serializers.CharField(source="award_description")

    class Meta:
        model = Achievements
        fields = ["year", "image", "title", "description"]

    def get_year(self, obj):
        return str(obj.award_winning_year)

    def get_title(self, obj):
        return f"{obj.award_name} - {obj.award_of}" if obj.award_of else obj.award_name
    
class BlogSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source='blog_banner_picture')
    author = serializers.CharField(source='writer_name')
    category = serializers.SerializerMethodField()
    description = serializers.CharField(source='short_description')

    class Meta:
        model = Blog
        fields = ['image', 'date', 'author', 'category', 'title', 'description']

    def get_category(self, obj):
        return obj.category.blog_category if obj.category else ''
