from channels.generic.websocket import AsyncWebsocketConsumer
import json


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]

        print("🔥 USER:", user)
        print("🔥 USER ID:", user.id)

        if user.is_anonymous:
            print("❌ ANONYMOUS USER")
            await self.close()
            return

        self.group_name = f"user_{user.id}"

        print("🔥 GROUP:", self.group_name)

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )


    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'task_id': event['task_id'],
            'is_admin': event.get('is_admin', False),
            'username': event.get('username', 'User')
        }))