# story_app/models.py

import uuid
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone

# Layihədəki Custom User modeli
User = settings.AUTH_USER_MODEL

class Story(models.Model):
    """
    - Hər bir story üçün: image və ya video (max 60s)
    - Avtomatik 24 saat sonra məzmun passiv olur (is_active False)
    - İstifadəçi əllə arxivləyə və ya yenidən aktivləşdirə bilər
    - Görünmə məhdudiyyətləri və gizlətmə siyahısı
    """
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    media = models.FileField(upload_to='story_app/media/')  # Fayl saxlanma yolu
    media_type = models.CharField(
        max_length=5,
        choices=[('image','Image'), ('video','Video')],
        help_text='Mediya tipini qeyd edir'
    )
    caption = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(editable=False)
    is_archived = models.BooleanField(
        default=False,
        help_text='Əllə arxivlənmiş halları göstərir'
    )

    # Görünmə seçimləri
    VISIBILITY_CHOICES = [
        ('public','Public'),
        ('followers','Followers'),
        ('favorites','Favorites'),
        ('custom','Custom'),
    ]
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='followers',
        help_text='Kimin görə biləcəyini təyin edir'
    )
    hidden_from = models.ManyToManyField(
        User,
        related_name='hidden_stories',
        blank=True,
        help_text='Həmin istifadəçilərə story göstərilməyəcək'
    )

    def save(self, *args, **kwargs):
        # İlk dəfə yaradıldıqda expires_at = created_at + 24h
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """
        - True: 24 saat içində və arxivlənməmiş
        - False: zaman bitib və ya is_archived=True
        """
        now = timezone.now()
        return (not self.is_archived) and (self.created_at <= now < self.expires_at)

    def __str__(self):
        return f"Story {self.id} by {self.user.username}"

class StoryView(models.Model):
    """
    - Hər bir user üçün yalnız bir baxış qeydə alınır (unique_together)
    - İlk baxış vaxtı viewed_at-da saxlanır
    """
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('story','user')

class Highlight(models.Model):
    """
    - Arxivlənmiş story-lərdən istifadəçi tərəfindən kolleksiya
    - Ad unikaldır (hər istifadəçi üçün ayrı)
    """
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='highlights')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user','name')

    def __str__(self):
        return f"Highlight '{self.name}' by {self.user.username}"

class HighlightItem(models.Model):
    """
    - Hər bir Highlight içərisinə story əlavə edir
    - Təkrar story əlavə olunmur (unique_together)
    """
    highlight = models.ForeignKey(Highlight, on_delete=models.CASCADE, related_name='items')
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('highlight','story')
