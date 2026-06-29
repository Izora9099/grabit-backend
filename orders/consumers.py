import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        other_id = self.scope["url_route"]["kwargs"]["user_id"]
        try:
            other_id = int(other_id)
        except (ValueError, TypeError):
            await self.close(code=4004)
            return

        self._user = user
        uid1, uid2 = sorted([user.id, other_id])
        self.group_name = f"chat_{uid1}_{uid2}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # Receive-only consumer — messages are sent via the REST API
        pass

    async def message_new(self, event):
        await self.send(text_data=json.dumps({
            "type": "message.new",
            "id": event["id"],
            "sender_id": event["sender_id"],
            "sender_name": event["sender_name"],
            "body": event["body"],
            "created_at": event["created_at"],
        }))
