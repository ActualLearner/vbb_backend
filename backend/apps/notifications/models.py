import uuid

from django.db import models
from django.utils import timezone

from users.models import Facility, User


class NotificationType(models.TextChoices):
    """Categories of notification event (SDS 4.8 NotificationType)."""

    NEW_REQUEST = "NEW_REQUEST", "New blood request"
    REQUEST_ACCEPTED = "REQUEST_ACCEPTED", "Request accepted"
    REQUEST_REJECTED = "REQUEST_REJECTED", "Request rejected"
    REQUEST_IN_TRANSIT = "REQUEST_IN_TRANSIT", "Request in transit"
    REQUEST_FULFILLED = "REQUEST_FULFILLED", "Request fulfilled"
    REQUEST_CANCELLED = "REQUEST_CANCELLED", "Request cancelled"
    LOW_STOCK = "LOW_STOCK", "Low stock alert"
    EXPIRING_SOON = "EXPIRING_SOON", "Units expiring soon"


class NotificationEvent(models.Model):
    """A lightweight domain event record for notifications.

    Transitions emit NotificationEvent rows; delivery (push) is handled
    by delivery adapters which read and dispatch these events.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=64)
    notification_type = models.CharField(
        max_length=32,
        choices=NotificationType.choices,
        default=NotificationType.NEW_REQUEST,
    )
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

    A `NotificationEvent` is a domain event emitted by transitions. A
    `NotificationRecord` represents a delivered notification for a specific
    user and stores read/delivery metadata.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
