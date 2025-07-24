# story_app/urls.py

"""
URL routing for story_app:
- /api/stories/...       → StoryViewSet
- /api/highlights/...    → HighlightViewSet
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import StoryViewSet, HighlightViewSet

router = DefaultRouter()
router.register(r'stories', StoryViewSet, basename='stories')
router.register(r'highlights', HighlightViewSet, basename='highlights')

# urlpatterns = [
#     path('stories/', include((router.urls, 'story_app'), namespace='stories')),
#     path('highlights/', include((router.urls, 'story_app'), namespace='highlights')),
# ]

urlpatterns = [
    path('', include(router.urls)),
]