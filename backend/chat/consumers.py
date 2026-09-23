from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db.models import Q
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from .models import Conversation
from .serializers import MessageSerializer
from .views import conversation_group


@database_sync_to_async
def authorized_user(token, conversation_id):
    authentication = JWTAuthentication()
    try:
        user = authentication.get_user(authentication.get_validated_token(token))
    except (InvalidToken, AuthenticationFailed):
        # Invalid credentials must never expose conversation existence.
        return None
    if Conversation.objects.filter(pk=conversation_id).filter(
        Q(buyer=user) | Q(seller=user)
    ).exists():
        return user
    return None


@database_sync_to_async
def save_message(conversation_id, sender, content):
    conversation = Conversation.objects.get(pk=conversation_id)
    serializer = MessageSerializer(data={"content": content})
    serializer.is_valid(raise_exception=True)
    message = serializer.save(conversation=conversation, sender=sender)
    conversation.save(update_fields=["updated_at"])
    return MessageSerializer(message).data


class ConversationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        tokens = parse_qs(self.scope["query_string"].decode()).get("token", [])
        if not tokens:
            await self.close(code=4401)
            return
        self.user = await authorized_user(tokens[0], self.conversation_id)
        if self.user is None:
            await self.close(code=4403)
            return
        self.group_name = conversation_group(self.conversation_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if not isinstance(content, dict) or content.get("type") != "message":
            await self.send_json({"type": "error", "detail": "Expected type 'message'."})
            return
        try:
            data = await save_message(
                self.conversation_id, self.user, content.get("content", "")
            )
        except ValidationError:
            await self.send_json({"type": "error", "detail": "Invalid message."})
            return
        await self.channel_layer.group_send(
            self.group_name, {"type": "chat.message", "message": data}
        )

    async def chat_message(self, event):
        await self.send_json({"type": "message", "message": event["message"]})
