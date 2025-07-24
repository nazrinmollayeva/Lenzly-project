# story_app/apps.py

from django.apps import AppConfig

class StoryAppConfig(AppConfig):
    name = 'story_app'

    def ready(self):
        import story_app.signals
