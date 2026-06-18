from unittest import mock

from django.test import TestCase
from notifications.delivery import DeliveryService, FcmAdapter
from notifications.models import NotificationEvent, NotificationRecord, NotificationType

from tests.factories import create_facility, create_user


class FcmAdapterTests(TestCase):
    def setUp(self):
        self.facility = create_facility(name="N", woreda=1)
        self.user = create_user(
            username="n", facility=self.facility, device_token="tok-123"
        )
        self.event = NotificationEvent.objects.create(
            event_type="request_created",
            notification_type=NotificationType.NEW_REQUEST,
            facility=self.facility,
            payload={"message": "A new blood request arrived."},
        )

    def test_adapter_simulates_without_credentials(self):
        # No Firebase creds -> adapter is disabled and no-ops without raising.
        adapter = FcmAdapter()
        self.assertFalse(adapter.enabled)
        adapter.send(self.user, self.event)  # should not raise

    def test_delivery_creates_records_via_fcm_adapter(self):
        adapter = FcmAdapter()
        with mock.patch.object(adapter, "send") as mocked:
            created = DeliveryService(adapters=[adapter]).deliver_event(self.event)
        self.assertEqual(created, 1)
        mocked.assert_called_once()
        self.assertTrue(
            NotificationRecord.objects.filter(event=self.event, user=self.user).exists()
        )
        self.event.refresh_from_db()
        self.assertTrue(self.event.dispatched)

    def test_message_minimum_length_enforced(self):
        from notifications.delivery import _event_message

        short = NotificationEvent.objects.create(
            event_type="x",
            facility=self.facility,
            payload={"message": "hi"},
        )
        self.assertGreaterEqual(len(_event_message(short)), 10)
