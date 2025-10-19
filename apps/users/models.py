from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Facility(models.Model):
    """Represents a hospital, clinic, or blood bank."""

    name = models.CharField(max_length=255)
    region = models.CharField(max_length=100)
    zone = models.CharField(max_length=100)
    woreda = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(20),  # As requested, max of 20
        ]
    )
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    class Meta:
        # Small fix to make Django's admin panel say "Facilities" instead of "Facilitys"
        verbose_name_plural = "Facilities"

    def __str__(self):
        # This is what will be displayed in the Django admin panel for each facility
        return f"{self.name} (Woreda {self.woreda}, {self.zone})"


class User(AbstractUser):
    """
    Custom User model for verified healthcare professionals.
    By extending AbstractUser, we get all of Django's built-in authentication
    (passwords, permissions, etc.) but we can add our own custom fields.
    """

    # Using a TextChoices class makes our role choices clean and reusable
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "System Administrator"
        FACILITY_REPRESENTATIVE = "FACILITY_REPRESENTATIVE", "Facility Representative"

    role = models.CharField(max_length=50, choices=Role.choices)

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

    def __str__(self):
        return self.username
