from datetime import date, timedelta
import random

from users.models import Facility
from django.contrib.auth import get_user_model
from inventory.models import BloodUnit

User = get_user_model()


def create_facility(name="Test Facility", region="R", zone="Z", woreda=1):
    return Facility.objects.create(name=name, region=region, zone=zone, woreda=woreda)


def create_user(username='user', facility=None, role=None):
    if facility is None:
        facility = create_facility()
    return User.objects.create_user(username=username, password='password', facility=facility, role=role or User.Role.FACILITY_REPRESENTATIVE)


def create_blood_unit(facility, blood_type='A+', days_until_expiry=10):
    return BloodUnit.objects.create(facility=facility, blood_type=blood_type, expires_at=(date.today() + timedelta(days=days_until_expiry)))
