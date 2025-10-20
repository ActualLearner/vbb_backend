from django.db import models
from django.utils import timezone
from users.models import Facility, User


class NotificationEvent(models.Model):
    """A lightweight domain event record for notifications.

    Transitions emit NotificationEvent rows; delivery (push/SMS) is handled
    by delivery adapters which read and dispatch these events.
    """

    event_type = models.CharField(max_length=64)
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name="notification_events",
        null=True,
        blank=True,
    )
    payload = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)
    dispatched = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"NotificationEvent<{self.event_type}> to {self.facility}"


class NotificationRecord(models.Model):
    """A user-scoped notification record for read/unread state.

    `NotificationEvent` is a domain event emitted by transitions. A
    `NotificationRecord` represents a delivered notification for a specific
    user and stores read/delivery metadata.
    """

    event = models.ForeignKey(
        NotificationEvent, on_delete=models.CASCADE, related_name="records"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    read = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-delivered_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return (
            f"NotificationRecord<{self.event_id}> for {self.user_id} (read={self.read})"
        )
