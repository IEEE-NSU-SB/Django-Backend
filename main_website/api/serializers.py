
from rest_framework import serializers
from main_website.models import Achievements

class AchievementSerializer(serializers.ModelSerializer):
    year = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    description = serializers.CharField(source="award_description")

    class Meta:
        model = Achievements
        fields = ["year", "image", "title", "description"]

    def get_year(self, obj):
        return str(obj.award_winning_year)

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.award_picture and hasattr(obj.award_picture, "url"):
            return request.build_absolute_uri(obj.award_picture.url) if request else obj.award_picture.url
        return None

    def get_title(self, obj):
        return f"{obj.award_name} - {obj.award_of}" if obj.award_of else obj.award_name
