# post_app/serializers.py

from rest_framework import serializers
from .models import Post, PostMedia, Like, Comment

class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = ['id', 'file', 'media_type']

class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'username', 'text', 'created_at']

class LikeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'username', 'created_at']

class PostSerializer(serializers.ModelSerializer):
    # uid = serializers.UUIDField(read_only=True)
    media          = PostMediaSerializer(many=True, read_only=True)
    likes_count    = serializers.IntegerField(source='likes.count', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    comments       = CommentSerializer(many=True, read_only=True)
    is_liked       = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'caption', 'created_at', 'is_archived'
            # , 'uid'
            , 'media', 'likes_count', 'comments_count', 'comments', 'is_liked'
        ]
        read_only_fields = [
            'author', 'created_at',
            'likes_count', 'comments_count', 'comments', 'is_liked'
        ]

    def get_is_liked(self, obj):
        user = self.context['request'].user
        return obj.likes.filter(user=user).exists()

class PostCreateSerializer(serializers.ModelSerializer):
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=True,
        help_text='Up to 5 files (images or videos)'
    )

    class Meta:
        model = Post
        fields = ['caption', 'media_files']

    def validate_media_files(self, files):
        # 1) Siyahı boş ola bilməz
        if not files or len(files) == 0:
            raise serializers.ValidationError("At least one media file is required.")
        # 2) Maksimum 5 fayl
        if len(files) > 5:
            raise serializers.ValidationError("You can upload a maximum of 5 files.")
        return files

    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        user = self.context['request'].user
        post = Post.objects.create(author=user, **validated_data)
        for f in media_files:
            media_type = 'video' if f.content_type.startswith('video') else 'image'
            PostMedia.objects.create(post=post, file=f, media_type=media_type)
        return post
