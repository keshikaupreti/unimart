import asyncio
from decimal import Decimal

from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from config.asgi import application
from listings.models import Category, Listing

from .models import Conversation, Message


def make_users_and_listing():
    user_model = get_user_model()
    seller = user_model.objects.create_user(
        username="seller", email="seller@example.com", password="password123"
    )
    buyer = user_model.objects.create_user(
        username="buyer", email="buyer@example.com", password="password123"
    )
    outsider = user_model.objects.create_user(
        username="outsider", email="outsider@example.com", password="password123"
    )
    category = Category.objects.create(name="Books", slug="books")
    listing = Listing.objects.create(
        seller=seller, category=category, title="Book",
        description="Used", price=Decimal("100.00"),
    )
    return seller, buyer, outsider, listing


class ConversationAPITests(TestCase):
    def setUp(self):
        self.seller, self.buyer, self.outsider, self.listing = make_users_and_listing()
        self.client = APIClient()

    def test_conversation_and_message_access(self):
        self.client.force_authenticate(self.buyer)
        response = self.client.post(
            "/api/conversations/", {"listing": str(self.listing.pk)}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        conversation_id = response.data["id"]
        self.assertEqual(response.data["seller"]["id"], str(self.seller.pk))
        self.assertEqual(
            self.client.post(
                "/api/conversations/", {"listing": str(self.listing.pk)}, format="json"
            ).status_code, 400,
        )
        self.assertEqual(
            self.client.post(
                f"/api/conversations/{conversation_id}/messages/",
                {"content": "  Is it available?  "}, format="json",
            ).status_code, 201,
        )
        self.assertEqual(Message.objects.get().content, "Is it available?")
        self.assertEqual(
            self.client.post(
                f"/api/conversations/{conversation_id}/messages/",
                {"content": "   "}, format="json",
            ).status_code, 400,
        )

        self.client.force_authenticate(self.outsider)
        self.assertEqual(self.client.get("/api/conversations/").data["count"], 0)
        self.assertEqual(
            self.client.get(f"/api/conversations/{conversation_id}/").status_code, 404
        )
        self.assertEqual(
            self.client.post(
                f"/api/conversations/{conversation_id}/messages/",
                {"content": "Spy"}, format="json",
            ).status_code, 404,
        )

        self.client.force_authenticate(self.seller)
        messages = self.client.get(
            f"/api/conversations/{conversation_id}/messages/"
        )
        self.assertEqual(messages.status_code, 200)
        self.assertEqual(messages.data["results"][0]["content"], "Is it available?")
        self.assertEqual(
            self.client.post(
                "/api/conversations/", {"listing": str(self.listing.pk)}, format="json"
            ).status_code, 400,
        )


class ConversationWebsocketTests(TransactionTestCase):
    def test_jwt_participants_receive_live_messages(self):
        seller, buyer, outsider, listing = make_users_and_listing()
        conversation = Conversation.objects.create(
            listing=listing, buyer=buyer, seller=seller
        )

        async def scenario():
            def communicator(user):
                token = str(AccessToken.for_user(user))
                return WebsocketCommunicator(
                    application,
                    f"/ws/conversations/{conversation.pk}/?token={token}",
                    headers=[(b"origin", b"http://testserver")],
                )

            buyer_socket = communicator(buyer)
            seller_socket = communicator(seller)
            outsider_socket = communicator(outsider)
            self.assertTrue((await buyer_socket.connect())[0])
            self.assertTrue((await seller_socket.connect())[0])
            self.assertFalse((await outsider_socket.connect())[0])

            await buyer_socket.send_json_to(
                {"type": "message", "content": "Hello seller"}
            )
            buyer_event = await buyer_socket.receive_json_from()
            seller_event = await seller_socket.receive_json_from()
            self.assertEqual(buyer_event["message"]["content"], "Hello seller")
            self.assertEqual(seller_event["message"]["content"], "Hello seller")
            self.assertEqual(buyer_event["message"]["sender"]["id"], str(buyer.pk))

            @database_sync_to_async
            def send_via_rest():
                client = APIClient()
                client.credentials(
                    HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(seller)}"
                )
                return client.post(
                    f"/api/conversations/{conversation.pk}/messages/",
                    {"content": "Yes, it is available"}, format="json",
                ).status_code

            self.assertEqual(await send_via_rest(), 201)
            self.assertEqual(
                (await buyer_socket.receive_json_from())["message"]["content"],
                "Yes, it is available",
            )
            self.assertEqual(
                (await seller_socket.receive_json_from())["message"]["content"],
                "Yes, it is available",
            )

            await buyer_socket.disconnect()
            await seller_socket.disconnect()

        asyncio.run(scenario())
        self.assertEqual(Message.objects.count(), 2)
