# profiles_system/serializers.py

from rest_framework import serializers
from django.conf import settings
from .models import Profile
from post_app.models import Post

User = settings.AUTH_USER_MODEL

class ProfileSerializer(serializers.ModelSerializer):
    is_private = serializers.BooleanField(read_only=False)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone_number = serializers.CharField(
        source='user.phone_number', read_only=True
    )
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'username', 'email', 'phone_number',
            'bio', 'profile_picture', 'show_phone',
            'is_private', 'created_at', 'post_count'
        ]
        read_only_fields = ['username', 'email', 'phone_number', 'created_at']

    def get_post_count(self, obj):
        return obj.user.posts.filter(is_archived=False).count()


class PublicProfileSerializer(serializers.ModelSerializer):
    is_private = serializers.BooleanField(read_only=True)
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    profile_picture = serializers.ImageField(read_only=True)
    bio = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    phone_number = serializers.SerializerMethodField()
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'user_id', 'username', 'profile_picture',
            'bio', 'created_at', 'is_private',
            'phone_number', 'post_count'
        ]

    def get_phone_number(self, obj):
        request = self.context.get('request', None)
        # 1) Anon user və ya request yoxdursa, göstərmə
        if not request or not request.user.is_authenticated:
            return None
        # 2) Sahibi özünüz show_phone=True etməlisiniz
        if not obj.show_phone:
            return None
        # 3) Sorğu edən profil obj-u favoritə alıbsa:
        caller_profile = getattr(request.user, 'profile', None)
        if not caller_profile:
            return None
        if not obj.favorited_by.filter(pk=caller_profile.pk).exists():
            return None
        # Hər üç şərt keçərli olduqda:
        return obj.user.phone_number

    def get_post_count(self, obj):
        user = obj.user
        # Arxivə salınmamış postların sayını götürür
        return user.posts.filter(is_archived=False).count()