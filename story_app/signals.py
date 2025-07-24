# story_app/signals.py

"""
Signals to automatically archive stories once expires_at is reached.
Uses Celery to schedule the archive task.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Story

@receiver(post_save, sender=Story)
def schedule_archive(sender, instance, created, **kwargs):
    if created:
        # Redis / Celery olmadan birbaşa çalışdır:

        from .tasks import archive_story
        # Əslində, burada da gecikmə istəsəniz time.sleep istifadə edə bilərsiniz,
        # amma sadəcə dərhal arxivləmə üçün:
        archive_story(instance.id)