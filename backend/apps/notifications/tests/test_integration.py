from django.core.management import call_command
from django.test import TestCase
from notifications.models import NotificationEvent, NotificationRecord
from rest_framework.test import APIClient

from tests.factories import create_facility, create_user


class NotificationIntegrationTests(TestCase):
    def setUp(self):
        self.facility = create_facility(
            name="Test Facility", region="R", zone="Z", woreda=1
        )
        self.user = create_user(username="u1", facility=self.facility)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_dispatch_creates_records_and_api_returns_them(self):
        ev = NotificationEvent.objects.create(
            event_type="TestEvent", facility=self.facility, payload={"message": "Hello"}
        )
        self.assertFalse(ev.dispatched)

        call_command("dispatch_notifications")

        ev.refresh_from_db()
        self.assertTrue(ev.dispatched)

        # Ensure a NotificationRecord exists for the user
        self.assertTrue(
            NotificationRecord.objects.filter(event=ev, user=self.user).exists()
        )

        resp = self.client.get("/api/v1/notifications/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(len(data) >= 1)
