from django.test import TestCase
from notifications.models import NotificationEvent, NotificationRecord
from rest_framework.test import APIClient

from tests.factories import create_facility, create_user


class NotificationRecordAPITests(TestCase):
    def setUp(self):
        self.facility = create_facility(name="Notif", woreda=1)
        self.user = create_user(username="notif-user", facility=self.facility)
        self.other = create_user(username="notif-other", facility=self.facility)

        self.event = NotificationEvent.objects.create(
            event_type="request_created",
            facility=self.facility,
            payload={"message": "Hi"},
        )
        self.record = NotificationRecord.objects.create(
            event=self.event, user=self.user
        )
        NotificationRecord.objects.create(event=self.event, user=self.other)

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_list_only_returns_own_records(self):
        resp = self.client.get("/api/v1/notifications/")
        self.assertEqual(resp.status_code, 200)
        ids = [r["id"] for r in resp.json()["results"]]
        self.assertEqual(ids, [str(self.record.id)])

    def test_mark_read_sets_flag(self):
        self.assertFalse(self.record.read)
        resp = self.client.post(f"/api/v1/notifications/{self.record.id}/mark_read/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.record.refresh_from_db()
        self.assertTrue(self.record.read)

    def test_cannot_mark_other_users_record(self):
        foreign = NotificationRecord.objects.create(event=self.event, user=self.other)
        resp = self.client.post(f"/api/v1/notifications/{foreign.id}/mark_read/")
        self.assertEqual(resp.status_code, 404)
