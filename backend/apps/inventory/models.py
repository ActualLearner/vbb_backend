import uuid

from django.conf import settings
from django.db import models

from users.models import Facility

from .config import BLOOD_TYPES


class BloodUnit(models.Model):
    class BloodType(models.TextChoices):
        A_POSITIVE = "A+", "A+"
        A_NEGATIVE = "A-", "A-"
        B_POSITIVE = "B+", "B+"
        B_NEGATIVE = "B-", "B-"
        AB_POSITIVE = "AB+", "AB+"
        AB_NEGATIVE = "AB-", "AB-"
        O_POSITIVE = "O+", "O+"
        O_NEGATIVE = "O-", "O-"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blood_type = models.CharField(max_length=3, choices=BloodType.choices)
    facility = models.ForeignKey(
        Facility, on_delete=models.CASCADE, related_name="blood_units"
    )
    donated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateField()

    def __str__(self):
        return f"{self.blood_type} unit at {self.facility.name}"


class BloodRequest(models.Model):
    class RequestStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"
        FULFILLED = "FULFILLED", "Fulfilled"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requesting_facility = models.ForeignKey(
        Facility, on_delete=models.PROTECT, related_name="sent_requests"
    )
    fulfilling_facility = models.ForeignKey(
        Facility, on_delete=models.PROTECT, related_name="received_requests"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="blood_requests",
    )
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES)
    units_requested = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )
    # Optional free-text from the requester (SRS VBB-IN-BRQ-005, SDS 4.6).
    notes = models.CharField(max_length=500, blank=True)
    # Optional reason supplied when a request is rejected (SRS VBB-IN-IBR-004).
    rejection_reason = models.CharField(max_length=255, blank=True)
    # Lifecycle timestamps (SRS DB-004).
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acceptance_timestamp = models.DateTimeField(null=True, blank=True)
    dispatch_timestamp = models.DateTimeField(null=True, blank=True)
    fulfillment_timestamp = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return (
            f"Request for {self.units_requested} unit(s) of {self.blood_type} "
            f"from {self.requesting_facility.name}"
        )


class BloodRequestStatusEvent(models.Model):
    """Append-only history of a request's status changes (SRS VBB-UC-005).

    Powers the "history of status changes with timestamps" detail view.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        BloodRequest, on_delete=models.CASCADE, related_name="status_events"
    )
    from_status = models.CharField(
        max_length=20, choices=BloodRequest.RequestStatus.choices, blank=True
    )
    to_status = models.CharField(
        max_length=20, choices=BloodRequest.RequestStatus.choices
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="request_status_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.request_id}: {self.from_status} -> {self.to_status}"
