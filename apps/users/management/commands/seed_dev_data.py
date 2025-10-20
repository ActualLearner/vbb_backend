import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

HOSPITAL_DATA = [
    {
        "name": "Black Lion Specialized Hospital",
        "region": "Addis Ababa",
        "zone": "Lideta Sub-City",
        "woreda": 3,
        "latitude": 9.0132,
        "longitude": 38.7617,
    },
    {
        "name": "Adama Hospital Medical College",
        "region": "Oromia",
        "zone": "East Shewa",
        "woreda": 5,
        "latitude": 8.5447,
        "longitude": 39.2721,
    },
    {
        "name": "Gondar University Specialized Hospital",
        "region": "Amhara",
        "zone": "Central Gondar",
        "woreda": 2,
        "latitude": 12.6000,
        "longitude": 37.4667,
    },
    {
        "name": "Hawassa University Comprehensive Specialized Hospital",
        "region": "Sidama",
        "zone": "Hawassa",
        "woreda": 1,
        "latitude": 7.0500,
        "longitude": 38.4667,
    },
    {
        "name": "Ayder Comprehensive Specialized Hospital",
        "region": "Tigray",
        "zone": "Mekelle",
        "woreda": 4,
        "latitude": 13.4900,
        "longitude": 39.4768,
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
        "Seed realistic development data (facilities + blood units). Run only in dev."
    )

    def handle(self, *args, **options):
        Facility = __import__("users").users.models.Facility
        BloodUnit = __import__("inventory").inventory.models.BloodUnit

        blood_types = list(BLOOD_TYPE_DISTRIBUTION.keys())
        weights = list(BLOOD_TYPE_DISTRIBUTION.values())

        self.stdout.write("\nSeeding realistic facility and blood unit data...")
        for data in HOSPITAL_DATA:
            facility, created = Facility.objects.get_or_create(
                name=data["name"], defaults=data
            )
            if not created:
                self.stdout.write(
                    f"  - Facility '{facility.name}' already exists. Skipping."
                )
                continue

            self.stdout.write(f"  - Created facility: {facility.name}")

            units_to_create = []
            total_units_for_facility = random.randint(150, 500)

            for _ in range(total_units_for_facility):
                chosen_blood_type = random.choices(blood_types, weights=weights, k=1)[0]
                expiry_date = (
                    timezone.now() + timedelta(days=random.randint(1, 42))
                ).date()

                units_to_create.append(
                    BloodUnit(
                        blood_type=chosen_blood_type,
                        facility=facility,
                        expires_at=expiry_date,
                    )
                )

            BloodUnit.objects.bulk_create(units_to_create)
            self.stdout.write(
                f"    - Seeded {len(units_to_create)} blood units "
                f"with realistic distribution."
            )

        self.stdout.write("\nDone seeding development data.")
