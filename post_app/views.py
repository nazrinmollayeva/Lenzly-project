# post_app/views.py

from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Post, Like, Comment
from .serializers import (
    PostSerializer, PostCreateSerializer,
    LikeSerializer, CommentSerializer
)
from follow_system.models import Follow  # privacy check via follow

User = get_user_model()

class PostViewSet(viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  ):
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'archive', 'unarchive']:
            return PostCreateSerializer
        return PostSerializer

    def list(self, request):
        user = request.user
        public_qs = Post.objects.filter(
            author__profile__is_private=False,
            is_archived=False
        )
        followees = Follow.objects.filter(
            follower=user, status='accepted'
        ).values_list('following', flat=True)
        private_qs = Post.objects.filter(
            author__id__in=followees,
            author__profile__is_private=True,
            is_archived=False
        )
        qs = (public_qs | private_qs).distinct().order_by('-created_at')
        serializer = PostSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        post = get_object_or_404(Post, pk=pk)
        if post.author.profile.is_private:
            if not Follow.objects.filter(
                follower=request.user,
                following=post.author,
                status='accepted'
            ).exists():
                return Response({'detail': 'You cannot view this post.'},
                                status=status.HTTP_403_FORBIDDEN)
        serializer = PostSerializer(post, context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        serializer = PostCreateSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        post = serializer.save()
        return Response(
            PostSerializer(post, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'], url_path='me')
    def my_posts(self, request):
        """
        GET /api/posts/me/
        Hal‑hazırda login olan istifadəçinin bütün (arxivə salınmamış) postlarını qaytarır.
        """
        qs = Post.objects.filter(author=request.user, is_archived=False).order_by('-created_at')
        serializer = PostSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path=r'user/(?P<user_id>[^/.]+)/posts')
    def posts_by_user(self, request, user_id=None):
        """
        GET /api/posts/user/{user_id}/posts/
        - Əgər target profil publicdirsə, onun bütün (unarchived) postları gəlir.
        - Əgər privatedirsə, yalnız sizin accepted follow requestiniz varsa.
        """
        # 1) Hədəf user-i tap
        target = get_object_or_404(User, pk=user_id)
        profile = getattr(target, 'profile', None)

        # 2) Privacy yoxlaması
        if profile and profile.is_private:
            from follow_system.models import Follow
            if not Follow.objects.filter(
                follower=request.user,
                following=target,
                status='accepted'
            ).exists():
                return Response(
                    {'detail': 'You cannot view posts of this private user.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # 3) Postları topla (only unarchived)
        qs = Post.objects.filter(author=target, is_archived=False).order_by('-created_at')
        serializer = PostSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='me/archived')
    def my_archived_posts(self, request):
        """
        GET /api/posts/me/archived/
        Hal‑hazırda login olan istifadəçinin arxivə salınmış postlarını qaytarır.
        """
        qs = Post.objects.filter(author=request.user, is_archived=True).order_by('-created_at')
        serializer = PostSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='archive')
    def archive(self, request, pk=None):
        post = get_object_or_404(Post, pk=pk, author=request.user)
        post.is_archived = True
        post.save(update_fields=['is_archived'])
        return Response({'detail': 'Post archived.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='unarchive')
    def unarchive(self, request, pk=None):
        post = get_object_or_404(Post, pk=pk, author=request.user)
        post.is_archived = False
        post.save(update_fields=['is_archived'])
        return Response({'detail': 'Post unarchived.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='like')
    def like(self, request, pk=None):
        post = get_object_or_404(Post, pk=pk)
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if not created:
            return Response({'detail': 'You already liked this post.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(LikeSerializer(like).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='unlike')
    def unlike(self, request, pk=None):
        post = get_object_or_404(Post, pk=pk)
        deleted, _ = Like.objects.filter(user=request.user, post=post).delete()
        if deleted:
            return Response({'detail': 'Like removed.'}, status=status.HTTP_200_OK)
        return Response({'detail': 'You have not liked this post.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='likers')
    def likers(self, request, pk=None):
        """
        GET /api/posts/{post_id}/likers/
        """
        post = get_object_or_404(Post, pk=pk)
        usernames = post.likes.values_list('user__username', flat=True).distinct()
        return Response({'usernames': list(usernames)}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='comment')
    def comment(self, request, pk=None):
        post = get_object_or_404(Post, pk=pk)
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(user=request.user, post=post)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'comments/(?P<comment_id>[^/.]+)/delete')
    def delete_comment(self, request, pk=None, comment_id=None):
        comment = get_object_or_404(
            Comment,
            pk=comment_id,
            post__pk=pk,
            user=request.user
        )
        comment.delete()
        return Response({'detail': 'Comment deleted.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='commenters')
    def commenters(self, request, pk=None):
        post = get_object_or_404(Post, pk=pk)
        names = post.comments.values_list('user__username', flat=True).distinct()
        return Response({'usernames': list(names)}, status=status.HTTP_200_OK)

