from django.test import TestCase
from notifications.delivery import DeliveryService, StdoutAdapter
from notifications.models import NotificationEvent, NotificationRecord
from users.models import Facility, User


class DummyAdapter(StdoutAdapter):
    def __init__(self):
        self.calls = []

    def send(self, user, event):
        self.calls.append((user.id, event.id))


class DeliveryServiceTests(TestCase):
    def setUp(self):
        self.facility = Facility.objects.create(
            name="DTest", region="R", zone="Z", woreda=1
        )
        self.user = User.objects.create_user(
            username="duser",
            password="p",
            facility=self.facility,
            role=User.Role.CLINICIAN,
        )

    def test_custom_adapter_is_called_and_records_created(self):
        ev = NotificationEvent.objects.create(
            event_type="UnitTest", facility=self.facility, payload={"message": "Hi"}
        )
        adapter = DummyAdapter()
        svc = DeliveryService(adapters=[adapter])

        created = svc.deliver_event(ev)

        self.assertEqual(created, 1)
        self.assertTrue(
            NotificationRecord.objects.filter(event=ev, user=self.user).exists()
        )
        self.assertEqual(len(adapter.calls), 1)
