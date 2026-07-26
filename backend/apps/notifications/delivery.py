import logging
import os

from django.utils import timezone

from users.models import User

from .models import NotificationEvent, NotificationRecord

logger = logging.getLogger(__name__)


def _event_message(event: NotificationEvent) -> str:
    """Return the human-readable message, honouring the SDS 4.8 length bounds.

    Messages must be between 10 and 500 characters; short payloads are padded
    with a generic suffix so downstream channels always have a usable body.
    """
    message = (event.payload.get("message") or "").strip()
    if len(message) < 10:
        message = f"{message} notification".strip()
    if len(message) < 10:
        message = "Notification update"
    return message[:500]


class Adapter:
    def send(self, user: User, event: NotificationEvent) -> None:
        raise NotImplementedError()


class StdoutAdapter(Adapter):
    """Phase-1 visibility adapter: logs delivery attempts (SRS 3.5.7)."""

    def send(self, user: User, event: NotificationEvent) -> None:
        logger.info(
            "NOTIFY type=%s to_facility=%s user=%s :: %s",
            event.notification_type,
            event.facility,
            user.id,
            _event_message(event),
        )


class FcmAdapter(Adapter):
    """Firebase Cloud Messaging push adapter (free tier).

    FCM delivers to both Android and iOS, so it is the sole push channel (SMS
    was dropped per SDS 1.3 contingency). Delivery is a no-op unless Firebase
    credentials are configured (GOOGLE_APPLICATION_CREDENTIALS or
    FIREBASE_CREDENTIALS) and the recipient has a device token; this keeps the
    pipeline functional in development without paid infrastructure.
    """

    _initialized = False

    def __init__(self):
        self.enabled = self._ensure_app()

    def _ensure_app(self) -> bool:
        if FcmAdapter._initialized:
            return True
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get(
            "FIREBASE_CREDENTIALS"
        )
        if not creds_path:
            return False
        try:
            import firebase_admin
            from firebase_admin import credentials

            if not firebase_admin._apps:
                firebase_admin.initialize_app(credentials.Certificate(creds_path))
            FcmAdapter._initialized = True
            return True
        except Exception:  # pragma: no cover - depends on external creds
            logger.exception("Failed to initialize Firebase app")
            return False

    def send(self, user: User, event: NotificationEvent) -> None:
        token = getattr(user, "device_token", "")
        if not self.enabled or not token:
            logger.info("[fcm:simulated] user=%s :: %s", user.id, _event_message(event))
            return
        try:  # pragma: no cover - requires live FCM credentials
            from firebase_admin import messaging

            messaging.send(
                messaging.Message(
                    token=token,
                    notification=messaging.Notification(
                        title=event.get_notification_type_display(),
                        body=_event_message(event),
                    ),
                    data={k: str(v) for k, v in event.payload.items()},
                )
            )
        except Exception:  # pragma: no cover - external
            logger.exception("FCM send failed for user %s", user.id)


_ADAPTER_REGISTRY = {
    "stdout": StdoutAdapter,
    "fcm": FcmAdapter,
    "push": FcmAdapter,  # backward-compatible alias
}


class DeliveryService:
    def __init__(self, adapters: list[Adapter] | None = None):
        if adapters is not None:
            self.adapters = adapters
        else:
            # Configure adapters via NOTIFICATION_ADAPTERS, a comma-separated
            # list like "stdout,fcm". Unknown names fall back to stdout.
            adapters_env = os.environ.get("NOTIFICATION_ADAPTERS", "stdout")
            names = [n.strip().lower() for n in adapters_env.split(",") if n.strip()]
            self.adapters = [
                _ADAPTER_REGISTRY.get(name, StdoutAdapter)() for name in names
            ]

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
            NotificationRecord.objects.create(
                event=event, user=user, delivered_at=timezone.now()
            )
            for adapter in self.adapters:
                try:
                    adapter.send(user, event)
                except Exception:
                    logger.warning(
                        "Adapter %s failed for user %s on event %s",
                        adapter.__class__.__name__,
                        user.id,
                        event.id,
                    )
            total += 1

        event.dispatched = True
        event.save(update_fields=["dispatched"])
        return total
