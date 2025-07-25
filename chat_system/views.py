# chat_system/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Conversation, Message, ConversationParticipant, MessageReadReceipt
from .serializers import (
    ConversationSerializer,
    ConversationCreateSerializer,
    MessageSerializer,
    MessageCreateSerializer,
)
from django.db import transaction
from django.db.models import Count
from django.contrib.auth import get_user_model


User = get_user_model()


class ConversationViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Conversation.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationSerializer

    def list(self, request):
        qs = request.user.conversations.all()
        serializer = ConversationSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request):
        import uuid
        other_id = request.data.get('other_user_id')
        user_id = request.user.id

        # other_user_id mövcud olmalıdır
        if not other_id:
            return Response({'detail': 'You must provide other_user_id.'}, status=status.HTTP_400_BAD_REQUEST)

        # UUID formatını yoxla
        try:
            other_uuid = uuid.UUID(str(other_id))
        except ValueError:
            return Response({'detail': 'other_user_id must be a valid UUID.'}, status=status.HTTP_400_BAD_REQUEST)

        # Özünlə eyni olmamalıdır
        if other_uuid == user_id:
            return Response({'detail': 'You cannot open a conversation with yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        participants = {user_id, other_uuid}

        # Mövcud danışığı yoxla
        existing = (
            ConversationParticipant.objects
                .filter(user_id__in=participants)
                .values('conversation_id')
                .annotate(cnt=Count('conversation_id'))
                .filter(cnt=2)
                .values_list('conversation_id', flat=True)
        )
        if existing:
            convo = Conversation.objects.get(pk=existing[0])
            serializer = ConversationSerializer(convo, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Yeni danışıq yarad
        convo = Conversation.objects.create()
        for uid in participants:
            ConversationParticipant.objects.create(conversation=convo, user_id=uid)

        serializer = ConversationSerializer(convo, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)(
                {'detail': 'You can only create a conversation with yourself and exactly one other user.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Deduplicate and convert to ints
        unique_ids = set(int(pid) for pid in participant_ids)
        # Check existing conversation
        cp_qs = (
            ConversationParticipant.objects
            .filter(user_id__in=unique_ids)
            .values('conversation_id')
            .annotate(cnt=Count('conversation_id'))
            .filter(cnt=2)
            .values_list('conversation_id', flat=True)
        )
        if cp_qs:
            convo = Conversation.objects.get(pk=cp_qs[0])
            serializer = ConversationSerializer(convo, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        # Create new conversation
        convo = Conversation.objects.create()
        for uid in unique_ids:
            ConversationParticipant.objects.create(conversation=convo, user_id=uid)
        serializer = ConversationSerializer(convo, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        convo = get_object_or_404(Conversation, pk=pk)

        # yalnız iştirakçılar görə bilər
        if not ConversationParticipant.objects.filter(conversation=convo, user=request.user).exists():
            return Response(
                {'detail': 'Siz bu chata daxil deyilsiz.'},
                status=status.HTTP_403_FORBIDDEN
            )

        msgs = convo.messages.all()
        serializer = MessageSerializer(msgs, many=True, context={'request': request})
        return Response(serializer.data)

class MessageViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Message.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer

    def create(self, request):
        # context-ə həm request, həm user əlavə edirik
        serializer = MessageCreateSerializer(
            data=request.data,
            context={'request': request, 'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        msg = serializer.save()
        return Response(
            MessageSerializer(msg).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        msg = get_object_or_404(Message, pk=pk)
        MessageReadReceipt.objects.get_or_create(message=msg, user=request.user)
        return Response(status=status.HTTP_200_OK)
