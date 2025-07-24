# story_app/views.py

from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Story, StoryView, Highlight, HighlightItem
from .serializers import (
    StorySerializer,
    StoryCreateSerializer,
    StoryViewSerializer,
    HighlightSerializer,
    HighlightItemSerializer
)

class StoryViewSet(viewsets.GenericViewSet,
                   mixins.CreateModelMixin,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin):
    """
    - list:       GET  /api/stories/             → Active stories visible to the user
    - create:     POST /api/stories/             → Upload a new story (max 100/day)
    - archive:    POST /api/stories/{id}/archive/
    - unarchive:  POST /api/stories/{id}/unarchive/
    - delete_active: DELETE /api/stories/{id}/delete_active/
    - view:       POST /api/stories/{id}/view/   → Register a unique view
    """
    permission_classes = [IsAuthenticated]
    queryset = Story.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return StoryCreateSerializer
        return StorySerializer

    def list(self, request):
        now = timezone.now()
        # Query param olaraq specific user_id istifadə oluna bilər
        user_id = request.query_params.get('user_id')
        qs = Story.objects.filter(
            is_archived=False,
            created_at__lte=now,
            expires_at__gt=now
        )
        if user_id:
            # Başqa istifadəçinin aktiv story-ləri
            qs = qs.filter(user__id=user_id)
        else:
            # Default: yalnız özünüzün aktiv story-ləri
            qs = qs.filter(user=request.user)
        serializer = StorySerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        serializer = StoryCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        story = serializer.save()
        return Response(StorySerializer(story, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        story = get_object_or_404(Story, pk=pk, user=request.user)
        story.is_archived = True
        story.save(update_fields=['is_archived'])
        return Response({'detail': 'Archived.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='archived')
    def archived(self, request):
        """
        GET /api/stories/archived/
        → Cari istifadəçinin bütün arxivlənmiş story-ləri
        """
        qs = Story.objects.filter(user=request.user, is_archived=True)
        serializer = StorySerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        story = get_object_or_404(Story, pk=pk, user=request.user)
        story.is_archived = False
        story.save(update_fields=['is_archived'])
        return Response({'detail': 'Unarchived.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], url_path='delete_active')
    def delete_active(self, request, pk=None):
        story = get_object_or_404(Story, pk=pk, user=request.user)
        story.delete()
        return Response({'detail': 'Deleted.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        story = get_object_or_404(Story, pk=pk)
        obj, created = StoryView.objects.get_or_create(
            story=story,
            user=request.user
        )
        serializer = StoryViewSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='views')
    def views(self, request, pk=None):
        """
        GET /api/stories/{story_id}/views/
        → Həmin story-ni kimin, hansı sırayla ilk dəfə baxdığını qaytarır.
        """
        story = get_object_or_404(Story, pk=pk)
        qs = story.views.select_related('user').order_by('viewed_at')
        data = [
            {
                'user_id': v.user.id,
                'username': v.user.username,
                'viewed_at': v.viewed_at
            }
            for v in qs
        ]
        return Response(data, status=status.HTTP_200_OK)

class HighlightViewSet(viewsets.GenericViewSet):
    """
    - create_highlight: POST   /api/highlights/create/      → Yeni highlight
    - list_highlights:  GET    /api/highlights/list/        → İstifadəçinin highlight-ları
    - delete_highlight: DELETE /api/highlights/{id}/delete/ → Highlight sil
    - add_item:         POST   /api/highlights/{id}/add_item/    → Story əlavə et
    - list_items:       GET    /api/highlights/{id}/items/       → Həmin highlight-dakı story-lər
    - remove_item:      DELETE /api/highlights/{id}/remove_item/ → Story çıxar
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='create')
    def create_highlight(self, request):
        serializer = HighlightSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        highlight = serializer.save(user=request.user)
        return Response(HighlightSerializer(highlight).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='list')
    def list_highlights(self, request):
        qs = Highlight.objects.filter(user=request.user)
        serializer = HighlightSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path='delete')
    def delete_highlight(self, request, pk=None):
        highlight = get_object_or_404(Highlight, pk=pk, user=request.user)
        highlight.delete()
        return Response({'detail': 'Highlight deleted.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='add_item')
    def add_item(self, request, pk=None):
        highlight = get_object_or_404(Highlight, pk=pk, user=request.user)
        story_id = request.data.get('story_id')
        story = get_object_or_404(Story, pk=story_id)
        if not story.is_archived:
            return Response({'detail': 'Only archived stories can be highlighted.'},
                            status=status.HTTP_400_BAD_REQUEST)
        item, created = HighlightItem.objects.get_or_create(
            highlight=highlight,
            story=story
        )
        return Response(HighlightItemSerializer(item).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='items')
    def list_items(self, request, pk=None):
        highlight = get_object_or_404(Highlight, pk=pk, user=request.user)
        items = highlight.items.select_related('story').all()
        serializer = HighlightItemSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], url_path='remove_item')
    def remove_item(self, request, pk=None):
        highlight = get_object_or_404(Highlight, pk=pk, user=request.user)
        story_id = request.data.get('story_id')
        item = get_object_or_404(HighlightItem, highlight=highlight, story_id=story_id)
        item.delete()
        return Response({'detail': 'Item removed.'}, status=status.HTTP_200_OK)
