# story_app/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import Story, StoryView, Highlight, HighlightItem

class StorySerializer(serializers.ModelSerializer):
    views_count = serializers.IntegerField(
        source='views.count',
        read_only=True,
        help_text='Unique viewer count'
    )
    is_active = serializers.BooleanField(
        read_only=True,
        help_text='True if within 24h and not manually archived'
    )

    class Meta:
        model = Story
        fields = [
            'id', 'user', 'media', 'media_type', 'caption',
            'created_at', 'expires_at', 'is_archived',
            'visibility', 'hidden_from', 'views_count', 'is_active'
        ]
        read_only_fields = [
            'user', 'created_at', 'expires_at', 'views_count', 'is_active'
        ]

class StoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = [
            'media', 'media_type', 'caption',
            'visibility', 'hidden_from'
        ]

    def validate(self, attrs):
        """
        Limit: hər gün maksimum 100 story.
        """
        user = self.context['request'].user
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = Story.objects.filter(user=user, created_at__gte=today_start).count()
        if count >= 100:
            raise serializers.ValidationError("Daily story limit reached.")
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class StoryViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryView
        fields = ['story', 'user', 'viewed_at']
        read_only_fields = ['viewed_at']

class HighlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Highlight
        fields = ['id', 'user', 'name', 'created_at']
        read_only_fields = ['user', 'created_at']

class HighlightItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = HighlightItem
        fields = ['highlight', 'story', 'added_at']
        read_only_fields = ['added_at']
