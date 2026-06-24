import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from donations.models import DonationCenter
from inventory.models import BloodUnit
from users.models import Facility, User

HOSPITAL_DATA = [
    {
        "name": "Black Lion Specialized Hospital",
        "region": "Addis Ababa",
        "zone": "Lideta Sub-City",
        "woreda": 3,
        "city": "Addis Ababa",
        "contact_phone": "+251111234501",
        "latitude": 9.0132,
        "longitude": 38.7617,
    },
    {
        "name": "Adama Hospital Medical College",
        "region": "Oromia",
        "zone": "East Shewa",
        "woreda": 5,
        "city": "Adama",
        "contact_phone": "+251111234502",
        "latitude": 8.5447,
        "longitude": 39.2721,
    },
    {
        "name": "Gondar University Specialized Hospital",
        "region": "Amhara",
        "zone": "Central Gondar",
        "woreda": 2,
        "city": "Gondar",
        "contact_phone": "+251111234503",
        "latitude": 12.6000,
        "longitude": 37.4667,
    },
    {
        "name": "Hawassa University Comprehensive Specialized Hospital",
        "region": "Sidama",
        "zone": "Hawassa",
        "woreda": 1,
        "city": "Hawassa",
        "contact_phone": "+251111234504",
        "latitude": 7.0500,
        "longitude": 38.4667,
    },
    {
        "name": "Ayder Comprehensive Specialized Hospital",
        "region": "Tigray",
        "zone": "Mekelle",
        "woreda": 4,
        "city": "Mekelle",
        "contact_phone": "+251111234505",
        "latitude": 13.4900,
        "longitude": 39.4768,
    },
]

DONATION_CENTERS = [
    {
        "name": "National Blood Bank Service - Addis Ababa",
        "city": "Addis Ababa",
        "operating_hours": "Mon-Sat 8AM-6PM",
        "contact_info": "+251115524948",
        "latitude": 9.0300,
        "longitude": 38.7400,
    },
    {
        "name": "Adama Regional Blood Bank",
        "city": "Adama",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "contact_info": "+251221110011",
        "latitude": 8.5400,
        "longitude": 39.2700,
    },
]

BLOOD_TYPE_DISTRIBUTION = {
    "A+": 34,
    "A-": 6,
    "B+": 9,
    "B-": 2,
    "AB+": 3,
    "AB-": 1,
    "O+": 38,
    "O-": 7,
}


class Command(BaseCommand):
    help = (
        "Seed realistic development data (facilities, users, blood units, "
        "donation centers). Run only in development."
    )

    def handle(self, *args, **options):
        blood_types = list(BLOOD_TYPE_DISTRIBUTION.keys())
        weights = list(BLOOD_TYPE_DISTRIBUTION.values())

        self.stdout.write("\nSeeding development data...")
        for idx, data in enumerate(HOSPITAL_DATA, start=1):
            facility, created = Facility.objects.get_or_create(
                name=data["name"], defaults=data
            )
            if not created:
                self.stdout.write(f"  - Facility '{facility.name}' exists. Skipping.")
                continue
            self.stdout.write(f"  - Created facility: {facility.name}")

            # One admin, one supply, and one clinician per facility.
            User.objects.create_user(
                username=f"admin{idx}",
                password="ChangeMe123!",
                role=User.Role.ADMIN,
                full_name=f"Admin {idx}",
                phone_number=f"+25191100000{idx}",
                facility=facility,
            )
            User.objects.create_user(
                username=f"supply{idx}",
                password="ChangeMe123!",
                role=User.Role.SUPPLY,
                full_name=f"Supply {idx}",
                phone_number=f"+25191200000{idx}",
                facility=facility,
            )
            User.objects.create_user(
                username=f"clinician{idx}",
                password="ChangeMe123!",
                role=User.Role.CLINICIAN,
                full_name=f"Clinician {idx}",
                phone_number=f"+25191300000{idx}",
                facility=facility,
            )

            units = []
            for _ in range(random.randint(150, 500)):
                chosen = random.choices(blood_types, weights=weights, k=1)[0]
                expiry = (timezone.now() + timedelta(days=random.randint(1, 42))).date()
                units.append(
                    BloodUnit(blood_type=chosen, facility=facility, expires_at=expiry)
                )
            BloodUnit.objects.bulk_create(units)
            self.stdout.write(f"    - Seeded {len(units)} blood units.")

        for data in DONATION_CENTERS:
            center, created = DonationCenter.objects.get_or_create(
                name=data["name"], defaults=data
            )
            if created:
                self.stdout.write(f"  - Created donation center: {center.name}")

        self.stdout.write("\nDone seeding development data.")
