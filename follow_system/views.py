# follow_system/views.py

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .models import Follow
from .serializers import FollowSerializer
from profiles_system.models import Profile

User = get_user_model()

class FollowViewSet(viewsets.GenericViewSet):
    """
    POST   /api/follow/request/   → Request to follow a user
    POST   /api/follow/accept/    → Accept a pending follow request
    POST   /api/follow/unfollow/  → Unfollow a user
    GET    /api/follow/followers/ → List users who follow you (accepted)
    GET    /api/follow/following/ → List users you follow (accepted)
    """
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='request')
    def follow_request(self, request):
        """
        Create a follow request: if target is public → accepted immediately,
        else → status='pending'.
        Body: { "user_id": "<target_user_uuid>" }
        """
        target_id = request.data.get('user_id')
        if not target_id:
            return Response(
                {"detail": "The 'user_id' field is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        target = get_object_or_404(User, id=target_id)
        me = request.user

        if target == me:
            return Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )

        follow_obj, created = Follow.objects.get_or_create(
            follower=me,
            following=target,
            defaults={'status': 'pending'}
        )

        if created and not target.profile.is_private:
            # Public hesabdırsa, avtomatik qəbul et
            follow_obj.status = 'accepted'
            follow_obj.save(update_fields=['status'])

        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(self.get_serializer(follow_obj).data, status=status_code)

    @action(detail=False, methods=['post'], url_path='accept')
    def accept(self, request):
        """
        Accept a pending follow request.
        Only the **followed** (target) user may call this on incoming pending requests.
        Body: { "user_id": "<follower_user_uuid>" }
        """
        follower_id = request.data.get('user_id')
        if not follower_id:
            return Response(
                {"detail": "The 'user_id' field is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Yalnız private hesabların requestləri var, publiclar üçün lazım deyil
        if not request.user.profile.is_private:
            return Response(
                {"detail": "Public accounts do not have follow requests to accept."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Yalnız target = request.user üçün və status 'pending' olanları axtar
        follow_obj = get_object_or_404(
            Follow,
            follower__id=follower_id,
            following=request.user,
            status='pending'
        )

        follow_obj.status = 'accepted'
        follow_obj.save(update_fields=['status'])
        return Response(self.get_serializer(follow_obj).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='unfollow')
    def unfollow(self, request):
        """
        Unfollow a user you are currently following.
        Body: { "user_id": "<target_user_uuid>" }
        """
        target_id = request.data.get('user_id')
        if not target_id:
            return Response(
                {"detail": "The 'user_id' field is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        target = get_object_or_404(User, id=target_id)
        deleted, _ = Follow.objects.filter(
            follower=request.user, following=target
        ).delete()

        if deleted:
            return Response(
                {"detail": "Unfollowed successfully."},
                status=status.HTTP_200_OK
            )
        return Response(
            {"detail": "You are not following this user."},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'], url_path='followers')
    def followers(self, request):
        """
        List users who follow you (only accepted).
        GET /api/follow/followers/
        """
        qs = Follow.objects.filter(following=request.user, status='accepted')
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='following')
    def following(self, request):
        """
        List users you follow (only accepted).
        GET /api/follow/following/
        """
        qs = Follow.objects.filter(follower=request.user, status='accepted')
        return Response(self.get_serializer(qs, many=True).data)
