# profiles_system/views.py

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Profile
from .serializers import ProfileSerializer, PublicProfileSerializer

class ProfileViewSet(viewsets.GenericViewSet):
    """
    /api/profile/me/          GET, PUT
    /api/profile/favorites/    GET
    /api/profile/favorites/add/ POST { "user_id": <id> }
    /api/profile/block/list/   GET
    /api/profile/block/add/    POST { "user_id": <id> }
    """
    queryset = Profile.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        return {'request': self.request}

    def get_serializer_class(self):
        if self.action in ['me', 'update_me']:
            return ProfileSerializer
        return PublicProfileSerializer

    def get_queryset(self):
        me = self.request.user.profile
        blocked   = set(me.blocked.values_list('pk', flat=True))
        blocked_by= set(me.blocked_by.values_list('pk', flat=True))
        return Profile.objects.exclude(pk__in=blocked | blocked_by)

    def list(self, request):
        """
        GET /api/profile/
        Bütün istifadəçi profillərini və onların user_id-lərini qaytarır.
        """
        qs = self.get_queryset()
        serializer = PublicProfileSerializer(
            qs, many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'put'], url_path='me')
    def me(self, request):
        profile = request.user.profile
        if request.method == 'GET':
            return Response(ProfileSerializer(profile).data)
        # PUT
        serializer = ProfileSerializer(
            instance=profile, data=request.data, partial=True,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='favorites/add')
    def favorites_add(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "The 'user_id' field is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        target = get_object_or_404(Profile, user__id=user_id)
        me = request.user.profile

        # 1) Özünü əlavə etmək istəmək qadağa
        if target == me:
            return Response({"detail": "You cannot favorite yourself."},
                            status=status.HTTP_400_BAD_REQUEST)

        # 2) Əgər qarşılıqlı blok varsa, əlavə etməyə icazə yoxdur
        if target in me.blocked.all() or target in me.blocked_by.all():
            return Response({"detail": "Cannot favorite a user you have blocked or who has blocked you."},
                            status=status.HTTP_403_FORBIDDEN)

        # 3) Əgər artıq favoritdədirsə, yenidən əlavə etmə
        if target in me.favorites.all():
            return Response({"detail": "This user is already in your favorites."},
                            status=status.HTTP_400_BAD_REQUEST)

        me.favorites.add(target)
        return Response({"detail": "User added to favorites."}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='favorites/remove')
    def favorites_remove(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'detail': "The 'user_id' field is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        target = get_object_or_404(Profile, user__id=user_id)
        me = request.user.profile

        if target not in me.favorites.all():
            return Response({'detail': "This user is not in your favorites."},
                            status=status.HTTP_400_BAD_REQUEST)

        me.favorites.remove(target)
        return Response({'detail': "User removed from favorites."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='block/list')
    def block_list(self, request):
        qs = request.user.profile.blocked.all()
        serializer = PublicProfileSerializer(qs, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='block/add')
    def block_add(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "The 'user_id' field is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        target = get_object_or_404(Profile, user__id=user_id)
        me = request.user.profile

        if target == me:
            return Response({"detail": "You cannot block yourself."},
                            status=status.HTTP_400_BAD_REQUEST)

        # 1) Əgər artıq bloklanıbsa
        if target in me.blocked.all():
            return Response({"detail": "This user is already blocked."},
                            status=status.HTTP_400_BAD_REQUEST)

        # 2) Blok edərkən favoritlərdən çıxar
        me.blocked.add(target)
        me.favorites.remove(target)

        return Response({"detail": "User blocked successfully."}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='block/remove')
    def block_remove(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "The 'user_id' field is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        target = get_object_or_404(Profile, user__id=user_id)
        me = request.user.profile

        if target not in me.blocked.all():
            return Response({"detail": "This user is not blocked."},
                            status=status.HTTP_400_BAD_REQUEST)

        me.blocked.remove(target)
        return Response({"detail": "User unblocked successfully."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='me/bio/remove')
    def bio_remove(self, request):
        """
        POST /api/profile/me/bio/remove/
        -> profildən bio sahəsini silir (blank edir).
        """
        profile = request.user.profile
        profile.bio = ''
        profile.save(update_fields=['bio'])
        return Response({'detail': 'Bio removed successfully.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='me/picture/remove')
    def picture_remove(self, request):
        """
        POST /api/profile/me/picture/remove/
        -> profildən profile_picture silir.
        """
        profile = request.user.profile
        # Faylı disklə də silmək üçün:
        if profile.profile_picture:
            profile.profile_picture.delete(save=False)
        profile.profile_picture = None
        profile.save(update_fields=['profile_picture'])
        return Response({'detail': 'Profile picture removed successfully.'},
                        status=status.HTTP_200_OK)