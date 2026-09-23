from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from listings.models import Category, Listing
from transactions.models import MeetupLocation, Transaction
from .models import Dispute, Report


class ModerationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.buyer = users.create_user(username="buyer", email="buyer@example.com")
        cls.seller = users.create_user(username="seller", email="seller@example.com")
        cls.other = users.create_user(username="other", email="other@example.com")
        cls.staff = users.create_user(username="staff", email="staff@example.com", is_staff=True)
        category = Category.objects.create(name="Books", slug="books")
        cls.listing = Listing.objects.create(seller=cls.seller, category=category, title="Book", description="Textbook", price="100")
        cls.sale = Transaction.objects.create(
            listing=cls.listing, buyer=cls.buyer, seller=cls.seller,
            meetup_location=MeetupLocation.objects.create(name="Library"),
            meetup_time=timezone.now() + timedelta(days=1), status="accepted",
        )

    def test_report_target_validation_and_reporter_privacy(self):
        self.assertEqual(self.client.get("/api/reports/").status_code, 401)
        self.client.force_authenticate(self.buyer)
        for target in ({}, {"reported_user": str(self.buyer.pk)}, {"listing": str(self.listing.pk), "reported_user": str(self.seller.pk)}):
            self.assertEqual(self.client.post("/api/reports/", {"reason": "scam", **target}, format="json").status_code, 400)
        response = self.client.post("/api/reports/", {"listing": str(self.listing.pk), "reason": "misleading", "status": "resolved"}, format="json")
        self.assertEqual(response.status_code, 201)
        report = Report.objects.get(pk=response.data["id"])
        self.assertEqual(report.status, "open")
        self.assertEqual(report.reporter, self.buyer)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get("/api/reports/").data["count"], 0)
        self.assertEqual(self.client.get(f"/api/reports/{report.pk}/").status_code, 404)

    def test_only_staff_can_review_resolve_or_reject_reports(self):
        report = Report.objects.create(reporter=self.buyer, listing=self.listing, reason="scam")
        self.client.force_authenticate(self.buyer)
        for action in ("review", "resolve", "reject"):
            self.assertEqual(self.client.post(f"/api/reports/{report.pk}/{action}/").status_code, 403)
        self.client.force_authenticate(self.staff)
        for action, expected in (("review", "under_review"), ("resolve", "resolved"), ("reject", "rejected")):
            response = self.client.post(f"/api/reports/{report.pk}/{action}/", {"admin_note": "Checked evidence"}, format="json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["status"], expected)
        report.refresh_from_db()
        self.assertEqual(report.resolved_by, self.staff)
        self.assertEqual(report.admin_note, "Checked evidence")

    def test_dispute_requires_participant_and_eligible_sale(self):
        payload = {"transaction": str(self.sale.pk), "reason": "payment", "description": "Payment disagreement"}
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post("/api/disputes/", payload, format="json").status_code, 400)
        self.client.force_authenticate(self.buyer)
        for state in ("requested", "cancelled", "rejected"):
            self.sale.status = state
            self.sale.save()
            self.assertEqual(self.client.post("/api/disputes/", payload, format="json").status_code, 400)
        self.sale.status = "completed"
        self.sale.save()
        self.assertEqual(self.client.post("/api/disputes/", payload, format="json").status_code, 201)

    def test_dispute_lifecycle_duplicate_prevention_and_privacy(self):
        payload = {"transaction": str(self.sale.pk), "reason": "payment", "description": "Payment disagreement"}
        self.client.force_authenticate(self.buyer)
        response = self.client.post("/api/disputes/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        dispute_id = response.data["id"]
        url = f"/api/disputes/{dispute_id}/"
        self.assertEqual(self.client.post("/api/disputes/", payload, format="json").status_code, 400)
        self.client.force_authenticate(self.seller)
        self.assertEqual(self.client.get(url).status_code, 200)
        for action in ("review", "resolve", "reject"):
            self.assertEqual(self.client.post(url + action + "/").status_code, 403)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get("/api/disputes/").data["count"], 0)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.post(url + "review/").data["status"], "under_review")
        response = self.client.post(url + "resolve/", {"admin_note": "Agreed outcome"}, format="json")
        self.assertEqual(response.status_code, 200)
        dispute = Dispute.objects.get(pk=dispute_id)
        self.assertEqual(dispute.resolved_by, self.staff)
        self.assertEqual(dispute.admin_note, "Agreed outcome")
        self.client.force_authenticate(self.buyer)
        self.assertEqual(self.client.post("/api/disputes/", payload, format="json").status_code, 201)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.post(url + "review/").status_code, 400)
