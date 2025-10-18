from django.db import models
from django.conf import settings
from users.models import Facility


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
        APPROVED = "APPROVED", "Approved"
        FULFILLED = "FULFILLED", "Fulfilled"
        CANCELLED = "CANCELLED", "Cancelled"
        REJECTED = "REJECTED", "Rejected"

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
    blood_type = models.CharField(max_length=3, choices=BloodUnit.BloodType.choices)
    units_requested = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Request for {self.units_requested} unit(s) of {self.blood_type} from {self.requesting_facility.name}"
