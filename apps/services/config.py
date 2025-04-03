PAYSTACK_SECRET_KEY = "your_paystack_secret_key"
BUDPAY_API_KEY = "your_budpay_secret_key"
AMADEUS_API_SECRET = "your_amadeus_secret_key"

# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "notifications", self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "notifications", self.channel_name
        )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["message"]))