# follow_system/models.py

from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Follow(models.Model):
    STATUS_CHOICES = [('pending','Pending'),('accepted','Accepted')]
    follower  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    status    = models.CharField(max_length=8, choices=STATUS_CHOICES, default='pending')
    created_at= models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower','following')
