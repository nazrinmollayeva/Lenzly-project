# chat_system/serializers.py

"""
Serializers for Conversation and Message models.
"""
from rest_framework import serializers
from django.utils import timezone
from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageReadReceipt
)
from django.contrib.auth import get_user_model
User = get_user_model()

class MessageReadSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = MessageReadReceipt
        fields = ['user_id', 'username', 'read_at']

class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    read_receipts = MessageReadSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender_id', 'sender_username',
            'text', 'attachment', 'timestamp', 'read_receipts'
        ]
        read_only_fields = ['sender_id', 'timestamp', 'read_receipts']

class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['conversation', 'text', 'attachment']

    def validate_conversation(self, convo):
        user = self.context.get('user')
        if not user or not convo.participants.filter(id=user.id).exists():
            raise serializers.ValidationError('Not a participant in this conversation.')
        return convo

    def create(self, validated_data):
        validated_data['sender'] = self.context.get('user')
        return super().create(validated_data)

class ParticipantSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id')
    username = serializers.CharField(source='user.username')
    last_read_at = serializers.DateTimeField()
    is_muted = serializers.BooleanField()

    class Meta:
        model = ConversationParticipant
        fields = ['user_id', 'username', 'last_read_at', 'is_muted']

class ConversationSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(source='conversationparticipant_set', many=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'created_at', 'updated_at', 'last_message', 'unread_count']

    def get_last_message(self, convo):
        msg = convo.messages.last()
        if not msg:
            return None
        return MessageSerializer(msg).data

    def get_unread_count(self, convo):
        user = self.context['request'].user
        # Count messages after user's last_read
        try:
            cp = ConversationParticipant.objects.get(conversation=convo, user=user)
            return convo.messages.filter(timestamp__gt=cp.last_read_at).count()
        except ConversationParticipant.DoesNotExist:
            return 0

class ConversationCreateSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),  # integer yox, UUIDField istifadə edilir
        write_only=True
    )

    class Meta:
        model = Conversation
        fields = ['participant_ids']

    def validate_participant_ids(self, ids):
        if len(ids) != 2 or len(set(ids)) != 2:
            raise serializers.ValidationError('Provide exactly two distinct user IDs.')
        return ids

    def create(self, validated_data):
        user_ids = validated_data.pop('participant_ids')
        convo = Conversation.objects.create()
        convo.participants.set(User.objects.filter(id__in=user_ids))
        # Initialize ConversationParticipant entries
        for user in convo.participants.all():
            ConversationParticipant.objects.create(conversation=convo, user=user)
        return convo
