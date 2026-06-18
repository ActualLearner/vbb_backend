import uuid

from django.db import models


class DonationCenter(models.Model):
    """A physical location where blood donations can be made (SDS 4.9).

    Informational only: the VBB does not collect blood, it merely directs
    donors to active centers (SRS 3.2.4 / VBB-INV-004).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    # Address value object inlined (SDS 4.2): street/city + geo coordinates.
    street = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    operating_hours = models.CharField(max_length=255, blank=True)
    # Per SDS 4.9 contactInfo may be a phone number or an email address.
    contact_info = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.name} ({self.city})"
