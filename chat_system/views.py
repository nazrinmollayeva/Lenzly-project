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

    def create(self, request):
        serializer = ConversationCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        convo = serializer.save()
        return Response(ConversationSerializer(convo, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        convo = get_object_or_404(Conversation, pk=pk)
        qs = convo.messages.all()
        serializer = MessageSerializer(qs, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Message.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer

    def create(self, request):
        serializer = MessageCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        msg = serializer.save()
        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        msg = get_object_or_404(Message, pk=pk)
        # create read receipt
        MessageReadReceipt.objects.get_or_create(message=msg, user=request.user)
        return Response(status=status.HTTP_200_OK)