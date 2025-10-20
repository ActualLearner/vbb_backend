import os
from typing import List

from django.utils import timezone
from users.models import User

from .models import NotificationEvent, NotificationRecord


class Adapter:
    def send(self, user: User, event: NotificationEvent) -> None:
        raise NotImplementedError()


class StdoutAdapter(Adapter):
    def send(self, user: User, event: NotificationEvent) -> None:
        # Simple adapter for phase-1: write to stdout
        print("--- NOTIFICATION TRIGGERED ---")
        print(f"  Event: {event.event_type}")
        print(f"  To: Facility '{event.facility}'")
        print(f"  Details: {event.payload.get('message', 'No details')}")
        print("-----------------------------")


class PushAdapter(Adapter):
    def __init__(self, provider_url: str | None = None):
        self.provider_url = provider_url

    def send(self, user: User, event: NotificationEvent) -> None:
        # Stub: in phase-1 just log to stdout to simulate push delivery
        print(
            f"[push] Sending to user {user.id} via "
            f"{self.provider_url or 'default'}: {event.payload}"
        )


class SmsAdapter(Adapter):
    def __init__(self, provider_key: str | None = None):
        self.provider_key = provider_key

    def send(self, user: User, event: NotificationEvent) -> None:
        # Stub: in phase-1 just log to stdout to simulate SMS delivery
        print(
            f"[sms] Sending to user {user.id} using "
            f"{self.provider_key or 'default'}: {event.payload}"
        )


class DeliveryService:
    def __init__(self, adapters: List[Adapter] | None = None):
        # Default to stdout adapter if none provided
        if adapters is not None:
            self.adapters = adapters
        else:
            # Allow configuring adapters via the NOTIFICATION_ADAPTERS env var,
            # a comma-separated list like "stdout,push,sms". Unrecognized
            # names fall back to stdout.
            adapters_env = os.environ.get("NOTIFICATION_ADAPTERS", "stdout")
            names = [n.strip().lower() for n in adapters_env.split(",") if n.strip()]
            loaded = []
            for name in names:
                if name == "stdout":
                    loaded.append(StdoutAdapter())
                elif name == "push":
                    loaded.append(PushAdapter())
                elif name == "sms":
                    loaded.append(SmsAdapter())
                else:
                    loaded.append(StdoutAdapter())
            self.adapters = loaded

    def deliver_event(self, event: NotificationEvent) -> int:
        """Deliver an event to its recipients via all adapters.

        Returns the number of created NotificationRecord rows.
        """
        total = 0
        if event.facility_id:
            recipients = User.objects.filter(facility_id=event.facility_id)
        else:
            recipients = User.objects.all()

        for user in recipients:
            # create a NotificationRecord for this delivery
            NotificationRecord.objects.create(
                event=event, user=user, delivered_at=timezone.now()
            )
            for adapter in self.adapters:
                try:
                    adapter.send(user, event)
                except Exception:
                    # Phase 1: log failures to stdout and continue
                    print(f"Adapter failed for user {user.id} on event {event.id}")
            total += 1

        event.dispatched = True
        event.save(update_fields=["dispatched"])
        return total
