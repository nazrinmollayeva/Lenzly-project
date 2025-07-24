# story_app/tasks.py

from celery import shared_task
from django.utils import timezone
from .models import Story

@shared_task
def archive_story(story_id):
    try:
        story = Story.objects.get(id=story_id)
    except Story.DoesNotExist:
        return
    # Eğer hələ manual arxivlənməyibsə, expires_at keçdiyi üçün passive et
    if not story.is_archived and timezone.now() >= story.expires_at:
        story.is_archived = True
        story.save(update_fields=['is_archived'])

@shared_task
def archive_story_batch():
    now = timezone.now()
    Story.objects.filter(is_archived=False, expires_at__lte=now).update(is_archived=True)
