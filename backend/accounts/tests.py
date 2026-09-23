from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class AccountTests(APITestCase):
    def register(self, **overrides):
        data = {
            "username": "student", "email": "student@example.com",
            "password": "Maple!River82Trail", "first_name": "Student",
        }
        data.update(overrides)
        return self.client.post("/api/auth/register/", data, format="json")

    def test_registration_hashes_password_and_prevents_privilege_escalation(self):
        response = self.register(is_staff=True, is_superuser=True)
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.data)
        user = get_user_model().objects.get(username="student")
        self.assertTrue(user.check_password("Maple!River82Trail"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_registration_rejects_weak_passwords_and_duplicate_identity(self):
        for password in ("short", "123456789", "password123"):
            with self.subTest(password=password):
                self.assertEqual(self.register(password=password).status_code, 400)
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.register(email="another@example.com").status_code, 400)
        self.assertEqual(self.register(username="another").status_code, 400)

    def test_login_profile_refresh_rotation_and_logout(self):
        self.register()
        credentials = {"username": "student", "password": "Maple!River82Trail"}
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)
        self.assertEqual(self.client.post("/api/auth/login/", {**credentials, "password": "wrong"}).status_code, 401)
        response = self.client.post("/api/auth/login/", credentials)
        self.assertEqual(response.status_code, 200)
        tokens = response.data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = self.client.patch("/api/auth/me/", {"first_name": "Updated", "is_staff": True}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["first_name"], "Updated")
        self.assertFalse(get_user_model().objects.get(username="student").is_staff)
        rotated = self.client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]})
        self.assertEqual(rotated.status_code, 200)
        self.assertEqual(self.client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}).status_code, 401)
        refresh = rotated.data["refresh"]
        self.assertEqual(self.client.post("/api/auth/logout/", {"refresh": refresh}).status_code, 200)
        self.assertEqual(self.client.post("/api/auth/refresh/", {"refresh": refresh}).status_code, 401)
