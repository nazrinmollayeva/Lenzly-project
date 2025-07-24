# chat_system/consumers.py

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from .models import Conversation, Message
from .serializers import MessageSerializer, MessageCreateSerializer

User = get_user_model()

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f"chat_{self.conversation_id}"

        # Authenticate user
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return
        convo = await database_sync_to_async(Conversation.objects.get)(pk=self.conversation_id)
        participants = await database_sync_to_async(lambda: convo.participants.all())()
        if user not in participants:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content):
        user = self.scope['user']
        convo = await database_sync_to_async(Conversation.objects.get)(pk=self.conversation_id)

        # Serializer ilə yaratmaq
        serializer = MessageCreateSerializer(
            data={"conversation": convo.id, "text": content.get("text"), "attachment": None},
            context={"request": self.scope["request"]}  # Əgər burada request yoxdursa, sadəcə {"user": user} də verə bilərsiniz
        )
        # Validate & save
        if not serializer.is_valid():
            # səhvləri loglayın və ya client‑ə göndərin
            await self.send_json({"errors": serializer.errors})
            return

        msg = await database_sync_to_async(serializer.save)()

        data = MessageSerializer(msg).data
        # yenə group_send
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat.message", "message": data}
        )

    async def chat_message(self, event):
        await self.send_json(event['message'])