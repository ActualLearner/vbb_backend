from datetime import date, timedelta

from django.contrib.auth import get_user_model
from inventory.models import BloodUnit
from users.models import Facility

User = get_user_model()


def create_facility(name="Test Facility", region="R", zone="Z", woreda=1, **extra):
    return Facility.objects.create(
        name=name, region=region, zone=zone, woreda=woreda, **extra
    )


def create_user(username="user", facility=None, role=None, **extra):
    if facility is None:
        facility = create_facility()
    return User.objects.create_user(
        username=username,
        password="password",
        facility=facility,
        role=role or User.Role.PROFESSIONAL,
        **extra,
    )


def create_admin(username="admin", facility=None, **extra):
    return create_user(
        username=username, facility=facility, role=User.Role.ADMIN, **extra
    )


def create_blood_unit(facility, blood_type="A+", days_until_expiry=10):
    return BloodUnit.objects.create(
        facility=facility,
        blood_type=blood_type,
        expires_at=(date.today() + timedelta(days=days_until_expiry)),
    )
