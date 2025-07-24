# follow_system/serializers.py

from rest_framework import serializers
from .models import Follow

class FollowSerializer(serializers.ModelSerializer):
    follower_id  = serializers.UUIDField(source='follower.id', read_only=True)
    following_id = serializers.UUIDField(source='following.id', read_only=True)
    follower_username  = serializers.CharField(source='follower.username', read_only=True)
    following_username = serializers.CharField(source='following.username', read_only=True)
    class Meta:
        model = Follow
        fields = ['follower_id', 'follower_username', 'following_id', 'following_username', 'status','created_at']
