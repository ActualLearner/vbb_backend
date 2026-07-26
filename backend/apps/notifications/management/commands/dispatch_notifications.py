from django.core.management.base import BaseCommand

from notifications.delivery import DeliveryService
from notifications.models import NotificationEvent


class Command(BaseCommand):
    help = "Dispatch pending NotificationEvent rows to users (scheduled dispatcher)."

    def handle(self, *args, **options):
        pending = NotificationEvent.objects.filter(dispatched=False).order_by(
            "created_at"
        )[:1000]
        if not pending.exists():
            self.stdout.write("No pending notification events found.")
            return

        service = DeliveryService()
        total = 0
        for ev in pending:
            created = service.deliver_event(ev)
            self.stdout.write(
                f"Dispatched {created} records for event {ev.id} ({ev.event_type})"
            )
            total += created

        self.stdout.write(
            f"Dispatched {total} notification records from {pending.count()} events."
        )
