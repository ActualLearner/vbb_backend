import uuid

from core.validators import ethiopian_phone_validator
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from inventory.config import WOREDA_MAX, WOREDA_MIN


class Facility(models.Model):
    """Represents a hospital, clinic, or blood bank (SDS 4.1)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    # Ethiopian administrative hierarchy. `woreda` is the "district" the SDS
    # refers to; region/zone are retained for accuracy (see ADR-0006).
    region = models.CharField(max_length=100)
    zone = models.CharField(max_length=100)
    woreda = models.PositiveIntegerField(
        validators=[
            MinValueValidator(WOREDA_MIN),
            MaxValueValidator(WOREDA_MAX),
        ]
    )
    # Address value object inlined (SDS 4.2).
    street = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    contact_phone = models.CharField(
        max_length=20, blank=True, validators=[ethiopian_phone_validator]
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        # Small fix to make Django's admin panel say "Facilities" instead of "Facilitys"
        verbose_name_plural = "Facilities"

    def __str__(self):
        # This is what will be displayed in the Django admin panel for each facility
        return f"{self.name} (Woreda {self.woreda}, {self.zone})"


class User(AbstractUser):
    """Custom user for verified healthcare staff (SDS 4.3).

    Extends AbstractUser, inheriting password hashing, ``is_active`` (an
    inactive user cannot log in — SRS VBB-UC-007 4b), ``last_login`` and
    ``date_joined``. Adds an Ethiopian phone number (a login identifier per
    VBB-FUN-UM-004) and the RBAC role enforced by the API.
    """

    class Role(models.TextChoices):
        # Three least-privilege roles (supersedes the SDS 2-role matrix; see
        # ADR-0008). ADMIN manages users/facilities and reads everything but
        # performs no clinical actions. SUPPLY manages own-facility inventory
        # and fulfills incoming requests (accept/reject/ship). CLINICIAN raises
        # requests and confirms receipt (create/cancel/receive).
        ADMIN = "ADMIN", "Facility Administrator"
        SUPPLY = "SUPPLY", "Supply / Inventory Staff"
        CLINICIAN = "CLINICIAN", "Clinician"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLINICIAN)
    full_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        validators=[ethiopian_phone_validator],
    )
    # Newly provisioned accounts get a temporary password and must rotate it on
    # first login (SRS VBB-FUN-UM-002).
    must_change_password = models.BooleanField(default=False)
    # Registration token for FCM push delivery (nullable; set by the client).
    device_token = models.CharField(max_length=255, blank=True)

    # This links each user to one facility.
    # on_delete=models.PROTECT prevents us from accidentally deleting a facility
    # if there are still users assigned to it.
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name="staff",  # This lets us easily query facility.staff.all()
        null=True,  # Allows some users (like superadmins) to not have a facility
        blank=True,
    )

    @property
    def is_facility_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_supply(self) -> bool:
        return self.role == self.Role.SUPPLY

    @property
    def is_clinician(self) -> bool:
        return self.role == self.Role.CLINICIAN

    def __str__(self):
        return self.username
