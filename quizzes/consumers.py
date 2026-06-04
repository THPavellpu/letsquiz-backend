from channels.generic.websocket import AsyncWebsocketConsumer
import json


class LeaderboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.quiz_id = self.scope["url_route"]["kwargs"]["quiz_id"]
        self.group_name = f"leaderboard_{self.quiz_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.send(text_data=json.dumps({"message": "Connected to leaderboard"}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "Invalid JSON"}))
            return

        await self.send(text_data=json.dumps({"received": data}))

    async def leaderboard_update(self, event):
        print("LEADERBOARD EVENT RECEIVED")

        await self.send(
            text_data=json.dumps({
                "type": "leaderboard_update",
                "message": event["message"],
            })
        )