# post_app / models.py

import uuid
from django.db import models
from django.conf import settings
from profiles_system.models import Profile  # Profilin is_private və follow yoxlamaları üçün

User = settings.AUTH_USER_MODEL

class Post(models.Model):
    # uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True)
    author      = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='posts'
    )
    caption     = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)


    def __str__(self):
        return f"Post {self.id} by {self.author.username}"

class PostMedia(models.Model):
    MEDIA_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    post        = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='media'
    )
    file        = models.FileField(upload_to='post_app/media/')
    media_type  = models.CharField(max_length=5, choices=MEDIA_CHOICES)

    def __str__(self):
        return f"Media {self.id} for Post {self.post.id}"

class Like(models.Model):
    user       = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='likes'
    )
    post       = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} liked Post {self.post.id}"

class Comment(models.Model):
    user       = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments'
    )
    post       = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments'
    )
    text       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment {self.id} by {self.user.username} on Post {self.post.id}"
