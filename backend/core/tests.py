from django.test import TestCase

import uuid
from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import UUIDField
from django.utils import timezone

from chat.models import Conversation, Message
from listings.models import Category, Listing, ListingImage, SavedListing
from moderation.models import Dispute, Report
from reviews.models import Review
from transactions.models import MeetupLocation, Transaction


class UUIDPrimaryKeyTests(TestCase):
    def test_marketplace_models_use_uuid_primary_keys_and_foreign_keys(self):
        models = (
            get_user_model(), Category, Listing, ListingImage,
            MeetupLocation, Transaction, Review, Report, Dispute,
            SavedListing, Conversation, Message,
        )
        for model in models:
            with self.subTest(model=model.__name__):
                self.assertIsInstance(model._meta.pk, UUIDField)

        seller = get_user_model().objects.create_user(
            username="seller", email="seller@example.com", password="password123"
        )
        buyer = get_user_model().objects.create_user(
            username="buyer", email="buyer@example.com", password="password123"
        )
        category = Category.objects.create(name="Books", slug="books")
        listing = Listing.objects.create(
            seller=seller, category=category, title="Textbook",
            description="Used", price=Decimal("10.00"),
        )
        location = MeetupLocation.objects.create(name="Library")
        request = Transaction.objects.create(
            listing=listing, buyer=buyer, seller=seller,
            meetup_location=location,
            meetup_time=timezone.now() + timedelta(days=1),
        )
        self.assertIsInstance(request.pk, uuid.UUID)
        self.assertEqual(Transaction.objects.get(pk=request.pk).listing, listing)
        self.assertEqual(Transaction.objects.get(pk=request.pk).buyer, buyer)
