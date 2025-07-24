# chat_system/models.py

"""
Models for professional one-to-one chat system with read-tracking and conversation metadata.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Conversation(models.Model):
    """
    Stores metadata for a one-to-one chat between two users.
    """

    participants = models.ManyToManyField(
        User,
        through='ConversationParticipant',
        related_name='conversations',
        help_text='Exactly two participants per conversation'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        users = self.participants.all()
        return f"Conversation between {users[0].username} and {users[1].username}" if users.count() == 2 else f"Conversation {self.id}"

class ConversationParticipant(models.Model):
    """
    Through model to store per-user conversation settings and last read timestamp.
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_read_at = models.DateTimeField(default=timezone.make_aware(timezone.datetime.min))
    is_muted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('conversation', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.conversation.id}"

class Message(models.Model):
    """
    A message sent by a user within a conversation.
    Supports text and optional file attachments, with read status per recipient.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    text = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to='chat_system/attachments/',
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
        ]

    def __str__(self):
        preview = self.text[:20] + '...' if len(self.text) > 20 else self.text
        return f"Msg#{self.id} by {self.sender.username}: {preview}"

class MessageReadReceipt(models.Model):
    """
    Tracks which user has read which message and when.
    """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')
        indexes = [
            models.Index(fields=['read_at']),
        ]

    def __str__(self):
        return f"{self.user.username} read Msg#{self.message.id} at {self.read_at}"