from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Category, Listing, SavedListing


class SavedListingAPITests(TestCase):
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
            seller=self.seller, category=category, title="Book",
            description="Used", price=Decimal("100.00"),
        )
        self.client = APIClient()

    def test_save_list_delete_and_owner_privacy(self):
        self.client.force_authenticate(self.buyer)
        response = self.client.post(
            "/api/saved-listings/", {"listing": str(self.listing.pk)}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        saved_id = response.data["id"]
        self.assertEqual(SavedListing.objects.count(), 1)
        self.assertEqual(
            self.client.post(
                "/api/saved-listings/", {"listing": str(self.listing.pk)}, format="json"
            ).status_code, 400,
        )

        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get("/api/saved-listings/").data["count"], 0)
        self.assertEqual(
            self.client.get(f"/api/saved-listings/{saved_id}/").status_code, 404
        )

        self.client.force_authenticate(self.buyer)
        self.assertEqual(
            self.client.delete(f"/api/saved-listings/{saved_id}/").status_code, 204
        )
        self.assertEqual(SavedListing.objects.count(), 0)

    def test_seller_cannot_save_own_listing(self):
        self.client.force_authenticate(self.seller)
        response = self.client.post(
            "/api/saved-listings/", {"listing": str(self.listing.pk)}, format="json"
        )
        self.assertEqual(response.status_code, 400)


class RemovedListingVisibilityTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.seller = user_model.objects.create_user(
            username="seller", email="seller@example.com", password="password123"
        )
        self.buyer = user_model.objects.create_user(
            username="buyer", email="buyer@example.com", password="password123"
        )
        self.staff = user_model.objects.create_user(
            username="staff", email="staff@example.com", password="password123",
            is_staff=True,
        )
        category = Category.objects.create(name="Books", slug="books")
        self.removed = Listing.objects.create(
            seller=self.seller, category=category, title="Hidden textbook",
            description="Removed item", price=Decimal("100.00"),
            status=Listing.Status.REMOVED,
        )
        self.client = APIClient()

    def test_removed_listing_hidden_from_other_users_list_search_and_detail(self):
        url = f"/api/listings/{self.removed.pk}/"
        for user in (None, self.buyer):
            with self.subTest(user=user):
                self.client.force_authenticate(user=user)
                self.assertEqual(self.client.get(url).status_code, 404)
                self.assertEqual(
                    self.client.get("/api/listings/?status=removed&search=Hidden")
                    .data["count"], 0,
                )

        for user in (self.seller, self.staff):
            with self.subTest(user=user):
                self.client.force_authenticate(user=user)
                self.assertEqual(self.client.get(url).status_code, 200)
                self.assertEqual(
                    self.client.get("/api/listings/?status=removed").data["count"], 1
                )
