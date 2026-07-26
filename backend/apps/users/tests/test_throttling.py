from unittest import mock

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from tests.factories import create_facility, create_user

TINY_RATES = {"anon": "1000/min", "user": "1000/min", "auth": "3/min"}


def tiny_auth_rate():
    """Apply a tiny 'auth' throttle rate for the duration of a test.

    ``override_settings`` reloads DRF's api_settings, but SimpleRateThrottle
    captures ``DEFAULT_THROTTLE_RATES`` in a class attribute at import time,
    so the class attribute must be patched alongside the setting.
    """
    return (
        override_settings(
            REST_FRAMEWORK={
                **settings.REST_FRAMEWORK,
                "DEFAULT_THROTTLE_RATES": TINY_RATES,
            }
        ),
        mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", TINY_RATES),
    )


class LoginThrottleTests(TestCase):
    def setUp(self):
        self.facility = create_facility(name="Throttle", woreda=1)
        self.user = create_user(
            username="thr1",
            facility=self.facility,
            email="thr1@example.com",
        )
        self.client = APIClient()
        # Throttle history lives in the default cache; start clean and leave
        # clean so other tests are unaffected.
        cache.clear()
        self.addCleanup(cache.clear)

    def _login(self, password="wrong-password"):
        return self.client.post(
            "/api/v1/auth/login/",
            {"username": "thr1@example.com", "password": password},
            format="json",
        )

    def test_login_returns_429_when_auth_rate_exceeded(self):
        settings_ctx, rates_ctx = tiny_auth_rate()
        with settings_ctx, rates_ctx:
            # The first 3 attempts hit the credential check (401)...
            for _ in range(3):
                self.assertEqual(self._login().status_code, 401)
            # ...the 4th is throttled before credentials are even looked at.
            resp = self._login()
            self.assertEqual(resp.status_code, 429, resp.content)
            # Even a correct password is rejected while throttled.
            resp = self._login(password="password")
            self.assertEqual(resp.status_code, 429, resp.content)

    def test_login_not_throttled_under_the_limit(self):
        settings_ctx, rates_ctx = tiny_auth_rate()
        with settings_ctx, rates_ctx:
            for _ in range(2):
                self.assertEqual(self._login().status_code, 401)
            resp = self._login(password="password")
            self.assertEqual(resp.status_code, 200, resp.content)
