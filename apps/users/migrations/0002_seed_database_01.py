import random
from datetime import timedelta
from django.db import migrations
from django.utils import timezone

# --- CONFIGURATION ---

# A list of real Ethiopian hospitals to seed the database with.
HOSPITAL_DATA = [
    {
        "name": "Black Lion Specialized Hospital",
        "district": "Addis Ababa",
        "latitude": 9.0132,
        "longitude": 38.7617,
    },
    {
        "name": "Adama Hospital Medical College",
        "district": "Adama, Oromia",
        "latitude": 8.5447,
        "longitude": 39.2721,
    },
    {
        "name": "Gondar University Specialized Hospital",
        "district": "Gondar, Amhara",
        "latitude": 12.6000,
        "longitude": 37.4667,
    },
    {
        "name": "Hawassa University Comprehensive Specialized Hospital",
        "district": "Hawassa, SNNPR",
        "latitude": 7.0500,
        "longitude": 38.4667,
    },
    {
        "name": "Ayder Comprehensive Specialized Hospital",
        "district": "Mekelle, Tigray",
        "latitude": 13.4900,
        "longitude": 39.4768,
    },
]

# Approximate blood type distribution percentages (weights) for realistic data.
# This makes O+ and A+ far more common than AB-.
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

# --- MIGRATION FUNCTIONS ---


def seed_data(apps, schema_editor):
    """
    Seeds the database with Facility and BloodUnit data using a realistic
    distribution of blood types.
    """
    Facility = apps.get_model("users", "Facility")
    BloodUnit = apps.get_model("inventory", "BloodUnit")

    # Use these for weighted random choice
    blood_types = list(BLOOD_TYPE_DISTRIBUTION.keys())
    weights = list(BLOOD_TYPE_DISTRIBUTION.values())

    print("\nSeeding realistic facility and blood unit data...")
    for data in HOSPITAL_DATA:
        # Create the facility if it doesn't exist
        facility, created = Facility.objects.get_or_create(**data)
        if not created:
            print(f"  - Facility {facility.name} already exists. Skipping.")
            continue

        print(f"  - Created facility: {facility.name}")

        units_to_create = []
        # Each facility will have between 150 and 500 total blood units
        total_units_for_facility = random.randint(150, 500)

        for _ in range(total_units_for_facility):
            # Choose a blood type based on the realistic distribution
            chosen_blood_type = random.choices(blood_types, weights=weights, k=1)[0]

            # Blood units expire in 42 days, so set a random expiry date within that window
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

        # Use bulk_create for massive performance improvement.
        # This inserts all units in a single database query.
        BloodUnit.objects.bulk_create(units_to_create)
        print(
            f"    - Seeded {len(units_to_create)} blood units with realistic distribution."
        )


def unseed_data(apps, schema_editor):
    """
    Removes the data seeded by this migration, making it reversible.
    """
    Facility = apps.get_model("users", "Facility")
    facility_names = [data["name"] for data in HOSPITAL_DATA]

    # Deleting the facilities will automatically cascade and delete their blood units
    # due to the on_delete=models.CASCADE setting in the BloodUnit model.
    facilities_to_delete = Facility.objects.filter(name__in=facility_names)
    count = facilities_to_delete.count()
    facilities_to_delete.delete()
    print(
        f"\nUnseeded and removed {count} facilities and their associated blood units."
    )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
        # This data migration depends on the inventory models existing
        ("inventory", "0001_initial"),
    ]

    operations = [
        # The core of the migration: run our Python function.
        migrations.RunPython(seed_data, reverse_code=unseed_data),
    ]
