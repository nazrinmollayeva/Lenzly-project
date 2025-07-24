# chat_system/admin.py

from django.contrib import admin
from .models import Conversation, ConversationParticipant, Message, MessageReadReceipt

class ConversationParticipantInline(admin.TabularInline):
    model = ConversationParticipant
    extra = 0

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at')
    search_fields = ('conversationparticipant__user__username',)
    # Participants managed via through model inline
    inlines = [ConversationParticipantInline]

@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'user', 'last_read_at', 'is_muted')
    list_filter = ('is_muted',)
    search_fields = ('user__username',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'timestamp')
    search_fields = ('text', 'sender__username')
    list_filter = ('conversation',)

@admin.register(MessageReadReceipt)
class MessageReadReceiptAdmin(admin.ModelAdmin):
    list_display = ('message', 'user', 'read_at')
    search_fields = ('user__username',)
