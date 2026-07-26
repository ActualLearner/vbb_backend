from django.test import TestCase
from rest_framework.test import APIClient

from tests.factories import create_facility, create_user


class LogoutTests(TestCase):
    def setUp(self):
        self.facility = create_facility(name="Logout", woreda=1)
        self.user = create_user(
            username="out1",
            facility=self.facility,
            email="out1@example.com",
        )
        self.client = APIClient()

    def _login(self):
        resp = self.client.post(
            "/api/v1/auth/login/",
            {"username": "out1@example.com", "password": "password"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        return resp.json()

    def test_logout_blacklists_refresh_token(self):
        tokens = self._login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        resp = self.client.post(
            "/api/v1/auth/logout/", {"refresh": tokens["refresh"]}, format="json"
        )
        self.assertEqual(resp.status_code, 205, resp.content)
        # The blacklisted refresh token can no longer mint access tokens.
        resp = self.client.post(
            "/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json"
        )
        self.assertEqual(resp.status_code, 401, resp.content)

    def test_rotated_refresh_token_is_blacklisted(self):
        tokens = self._login()
        # Using the refresh token rotates it; the old one must stop working.
        resp = self.client.post(
            "/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json"
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        resp = self.client.post(
            "/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json"
        )
        self.assertEqual(resp.status_code, 401, resp.content)

    def test_logout_without_token_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post("/api/v1/auth/logout/", {}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_logout_with_garbage_token_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(
            "/api/v1/auth/logout/", {"refresh": "not-a-token"}, format="json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_logout_requires_authentication(self):
        resp = self.client.post(
            "/api/v1/auth/logout/", {"refresh": "whatever"}, format="json"
        )
        self.assertEqual(resp.status_code, 401)
