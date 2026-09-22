from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from listings.models import Category, Listing, ListingImage, SavedListing

from .models import MeetupLocation, Transaction


class PurchaseFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.seller = user_model.objects.create_user(
            username="seller", email="seller@example.com", password="password123"
        )
        self.buyer = user_model.objects.create_user(
            username="buyer", email="buyer@example.com", password="password123"
        )
        self.other = user_model.objects.create_user(
            username="other", email="other@example.com", password="password123"
        )
        category = Category.objects.create(name="Books", slug="books")
        self.listing = Listing.objects.create(
            seller=self.seller, category=category, title="BCA textbook",
            description="Good condition", price=Decimal("250.00"),
        )
        self.location = MeetupLocation.objects.create(name="Library Gate")
        self.client = APIClient()

    def request_purchase(self):
        self.client.force_authenticate(self.buyer)
        response = self.client.post(
            "/api/transactions/",
            {
                "listing": str(self.listing.pk),
                "meetup_location": str(self.location.pk),
                "meetup_time": (timezone.now() + timedelta(days=1)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        return response.data["id"]

    def test_request_accept_complete_review_and_listing_freeze(self):
        transaction_id = self.request_purchase()
        self.assertEqual(Transaction.objects.get(pk=transaction_id).status, "requested")

        self.client.force_authenticate(self.other)
        self.assertEqual(
            self.client.get(f"/api/transactions/{transaction_id}/").status_code, 404
        )

        self.client.force_authenticate(self.seller)
        self.assertEqual(
            self.client.post(f"/api/transactions/{transaction_id}/accept/")
            .status_code, 200,
        )
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.RESERVED)

        listing_url = f"/api/listings/{self.listing.pk}/"
        self.assertEqual(
            self.client.patch(listing_url, {"price": "1.00"}, format="json")
            .status_code, 403,
        )
        self.assertEqual(
            self.client.put(
                listing_url,
                {
                    "category": str(self.listing.category_id),
                    "title": "Changed title", "description": "Changed",
                    "price": "1.00", "condition": "poor",
                },
                format="json",
            ).status_code, 403,
        )
        image = ListingImage.objects.create(
            listing=self.listing, image="listings/example.png"
        )
        self.assertEqual(
            self.client.delete(f"/api/listing-images/{image.pk}/").status_code, 403
        )
        image_bytes = BytesIO()
        Image.new("RGB", (2, 2), "blue").save(image_bytes, "PNG")
        self.assertEqual(
            self.client.post(
                "/api/listing-images/",
                {
                    "listing": str(self.listing.pk),
                    "image": SimpleUploadedFile(
                        "new.png", image_bytes.getvalue(), content_type="image/png"
                    ),
                },
                format="multipart",
            ).status_code, 403,
        )
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.price, Decimal("250.00"))
        self.assertEqual(self.listing.title, "BCA textbook")
        self.assertTrue(ListingImage.objects.filter(pk=image.pk).exists())

        self.client.force_authenticate(self.buyer)
        self.assertEqual(
            self.client.post(f"/api/transactions/{transaction_id}/complete/")
            .status_code, 400,
        )
        self.client.force_authenticate(self.seller)
        self.assertEqual(
            self.client.post(f"/api/transactions/{transaction_id}/complete/")
            .status_code, 200,
        )
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.SOLD)
        self.assertEqual(
            self.client.patch(listing_url, {"price": "1.00"}, format="json")
            .status_code, 403,
        )

        self.client.force_authenticate(self.buyer)
        self.assertEqual(
            self.client.post(
                "/api/reviews/",
                {"transaction": str(transaction_id), "rating": 5}, format="json",
            ).status_code, 201,
        )
        self.assertEqual(
            self.client.post(
                "/api/reviews/",
                {"transaction": str(transaction_id), "rating": 4}, format="json",
            ).status_code, 400,
        )

    def test_cancelling_accepted_sale_reopens_listing_for_edits(self):
        transaction_id = self.request_purchase()
        self.client.force_authenticate(self.seller)
        self.assertEqual(
            self.client.post(f"/api/transactions/{transaction_id}/accept/")
            .status_code, 200,
        )
        self.client.force_authenticate(self.buyer)
        self.assertEqual(
            self.client.post(f"/api/transactions/{transaction_id}/cancel/")
            .status_code, 200,
        )
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.AVAILABLE)
        self.client.force_authenticate(self.seller)
        self.assertEqual(
            self.client.patch(
                f"/api/listings/{self.listing.pk}/",
                {"price": "225.00"}, format="json",
            ).status_code, 200,
        )
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.price, Decimal("225.00"))

    def test_deleting_listing_with_pending_requests_archives_and_rejects_them(self):
        first_id = self.request_purchase()
        self.client.force_authenticate(self.other)
        second = self.client.post(
            "/api/transactions/",
            {
                "listing": str(self.listing.pk),
                "meetup_location": str(self.location.pk),
                "meetup_time": (timezone.now() + timedelta(days=1)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(second.status_code, 201)
        SavedListing.objects.create(user=self.buyer, listing=self.listing)

        self.client.force_authenticate(self.seller)
        self.assertEqual(
            self.client.delete(f"/api/listings/{self.listing.pk}/").status_code, 204
        )
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.REMOVED)
        self.assertEqual(
            list(
                Transaction.objects.filter(
                    pk__in=[first_id, second.data["id"]]
                ).values_list("status", flat=True)
            ),
            [Transaction.Status.REJECTED, Transaction.Status.REJECTED],
        )
        self.assertFalse(SavedListing.objects.filter(listing=self.listing).exists())
        self.assertEqual(
            self.client.get(f"/api/listings/{self.listing.pk}/").status_code, 200
        )

        self.client.force_authenticate(self.buyer)
        self.assertEqual(
            self.client.get(f"/api/listings/{self.listing.pk}/").status_code, 404
        )
        self.assertEqual(
            self.client.get(f"/api/transactions/{first_id}/").data["status"],
            Transaction.Status.REJECTED,
        )

    def test_deleting_listing_without_requests_archives_it(self):
        self.client.force_authenticate(self.seller)
        self.assertEqual(
            self.client.delete(f"/api/listings/{self.listing.pk}/").status_code, 204
        )
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.REMOVED)
        self.client.force_authenticate(self.buyer)
        self.assertEqual(
            self.client.get(f"/api/listings/{self.listing.pk}/").status_code, 404
        )

    def test_actions_hide_missing_and_other_users_transactions(self):
        from uuid import uuid4

        transaction_id = self.request_purchase()
        self.client.force_authenticate(self.other)
        for target in (transaction_id, uuid4(), "invalid-uuid"):
            for action in ("accept", "cancel", "complete", "reject"):
                with self.subTest(target=target, action=action):
                    response = self.client.post(f"/api/transactions/{target}/{action}/")
                    self.assertEqual(response.status_code, 404)
        self.assertEqual(Transaction.objects.get(pk=transaction_id).status, "requested")
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, "available")
