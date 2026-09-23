from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from listings.models import Category, Listing
from transactions.models import MeetupLocation, Transaction
from .models import Review


class ReviewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.buyer = users.create_user(username="buyer", email="buyer@example.com")
        cls.seller = users.create_user(username="seller", email="seller@example.com")
        cls.other = users.create_user(username="other", email="other@example.com")
        listing = Listing.objects.create(seller=cls.seller, category=Category.objects.create(name="Books", slug="books"), title="Book", price="100")
        cls.sale = Transaction.objects.create(listing=listing, buyer=cls.buyer, seller=cls.seller, meetup_location=MeetupLocation.objects.create(name="Library"), meetup_time=timezone.now() + timedelta(days=1), status="completed")

    def test_review_requires_completed_sale_participant_and_valid_rating(self):
        payload = {"transaction": str(self.sale.pk), "rating": 5}
        self.assertEqual(self.client.post("/api/reviews/", payload).status_code, 401)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post("/api/reviews/", payload).status_code, 400)
        self.client.force_authenticate(self.buyer)
        for rating in (0, 6):
            self.assertEqual(self.client.post("/api/reviews/", {**payload, "rating": rating}).status_code, 400)
        self.sale.status = "accepted"
        self.sale.save()
        self.assertEqual(self.client.post("/api/reviews/", payload).status_code, 400)

    def test_both_participants_review_once_and_public_summary(self):
        for user, target, rating in ((self.buyer, self.seller, 5), (self.seller, self.buyer, 4)):
            self.client.force_authenticate(user)
            payload = {"transaction": str(self.sale.pk), "rating": rating}
            response = self.client.post("/api/reviews/", payload)
            self.assertEqual(response.status_code, 201)
            review = Review.objects.get(pk=response.data["id"])
            self.assertEqual(review.reviewed_user, target)
            self.assertEqual(self.client.post("/api/reviews/", payload).status_code, 400)
        self.client.force_authenticate(None)
        response = self.client.get(f"/api/reviews/summary/?user={self.seller.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["review_count"], 1)
        self.assertEqual(response.data["average_rating"], 5)
        self.assertEqual(self.client.get("/api/reviews/summary/?user=invalid").status_code, 400)
        self.assertEqual(self.client.get("/api/reviews/summary/").status_code, 400)
