# profiles_system/apps.py

from django.apps import AppConfig

class ProfileSystemConfig(AppConfig):
    name = 'profiles_system'

    def ready(self):
        import profiles_system.signals
