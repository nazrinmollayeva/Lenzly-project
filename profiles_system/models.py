# profiles_system/models.py
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(
        upload_to='profiles_system/profile_pictures/', null=True, blank=True
    )
    show_phone = models.BooleanField(
        default=False,
        help_text='If true, allows phone to be shown to favorites'
    )
    is_private = models.BooleanField(
        default = False,
        help_text = 'If true, only approved followers can see posts/stories'
    )
    favorites = models.ManyToManyField(
        'self', symmetrical=False, related_name='favorited_by', blank=True
    )
    blocked = models.ManyToManyField(
        'self', symmetrical=False, related_name='blocked_by', blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s Profile"
