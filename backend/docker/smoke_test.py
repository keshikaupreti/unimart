"""Exercise the Compose network and API; remove only the fixtures created here.

Run: docker compose exec -T backend python docker/smoke_test.py
"""

import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.docker_settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from listings.models import Category, Listing, ListingImage
from transactions.models import MeetupLocation, Transaction

ORIGIN = "http://frontend:3000"
run_id = uuid4().hex[:12]
password = f"Maple!{uuid4().hex}Trail"
users = []
category = None
location = None
listing_id = None


def request(path, *, method="GET", data=None, token=None, body=None, content_type=None, expected=200):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    elif content_type:
        headers["Content-Type"] = content_type
    req = Request(ORIGIN + path, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=20) as response:
            status = response.status
            payload = response.read()
            response_type = response.headers.get("Content-Type", "")
    except HTTPError as exc:
        status, payload, response_type = exc.code, exc.read(), ""
    if status != expected:
        raise AssertionError(f"{method} {path}: expected {expected}, got {status}: {payload[:300]!r}")
    return json.loads(payload) if "application/json" in response_type else payload


try:
    assert b"UniMart" in request("/")
    request("/api/categories/")
    for role in ("seller", "buyer"):
        username = f"docker_{role}_{run_id}"
        result = request("/api/auth/register/", method="POST", data={
            "username": username, "email": f"{username}@example.com", "password": password,
        }, expected=201)
        users.append(result["id"])
    seller, buyer = [request("/api/auth/login/", method="POST", data={
        "username": f"docker_{role}_{run_id}", "password": password,
    })["access"] for role in ("seller", "buyer")]
    request("/api/auth/me/", token=buyer)
    category = Category.objects.create(name=f"Docker check {run_id}", slug=f"docker-{run_id}")
    location = MeetupLocation.objects.create(name=f"Docker library {run_id}")
    listing = request("/api/listings/", method="POST", token=seller, data={
        "title": "Temporary container verification item", "description": "Removed after verification.",
        "category": str(category.pk), "price": "100.00", "condition": "good",
    }, expected=201)
    listing_id = listing["id"]

    # Upload and retrieve an image through the frontend proxy and media volume.
    from io import BytesIO
    from PIL import Image
    image = BytesIO()
    Image.new("RGB", (2, 2), "green").save(image, format="PNG")
    boundary = f"unimart-{run_id}"
    multipart = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"listing\"\r\n\r\n{listing_id}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"check.png\"\r\n"
        "Content-Type: image/png\r\n\r\n"
    ).encode() + image.getvalue() + f"\r\n--{boundary}--\r\n".encode()
    uploaded = request("/api/listing-images/", method="POST", token=seller, body=multipart,
                       content_type=f"multipart/form-data; boundary={boundary}", expected=201)
    media_path = "/media/" + uploaded["image"].split("/media/", 1)[1]
    assert request(media_path) == image.getvalue()

    sale = request("/api/transactions/", method="POST", token=buyer, data={
        "listing": listing_id, "meetup_location": str(location.pk), "meetup_time": "2099-01-01T12:00:00Z",
    }, expected=201)
    sale_path = f"/api/transactions/{sale['id']}/"
    assert request(sale_path + "accept/", method="POST", token=seller)["status"] == "accepted"
    assert request(sale_path + "complete/", method="POST", token=seller)["status"] == "completed"
    request("/api/reviews/", method="POST", token=buyer,
            data={"transaction": sale["id"], "rating": 5, "comment": "Container check"}, expected=201)
    request("/api/disputes/", method="POST", token=buyer, data={
        "transaction": sale["id"], "reason": "other", "description": "Container check",
    }, expected=201)
    request("/api/reports/", method="POST", token=buyer, data={
        "listing": listing_id, "reason": "other", "description": "Container check",
    }, expected=201)
    print("PASS: frontend, API proxy, authentication, image upload/retrieval, purchase lifecycle, reviews, disputes, and reports.")
finally:
    if listing_id:
        for image in ListingImage.objects.filter(listing_id=listing_id):
            image.image.delete(save=False)
        Transaction.objects.filter(listing_id=listing_id).delete()
        Listing.objects.filter(pk=listing_id).delete()
    if location:
        location.delete()
    if category:
        category.delete()
    get_user_model().objects.filter(pk__in=users).delete()
