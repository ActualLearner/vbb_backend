from django.test import TestCase
from rest_framework.test import APIClient

from donations.models import DonationCenter
from tests.factories import create_facility, create_user


class DonationCenterAPITests(TestCase):
    def setUp(self):
        self.facility = create_facility(name="F", woreda=1)
        self.user = create_user(username="u", facility=self.facility)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        # Addis (~9.03, 38.74) and Mekelle (~13.49, 39.47)
        self.addis = DonationCenter.objects.create(
            name="Addis Center",
            city="Addis Ababa",
            latitude=9.0300,
            longitude=38.7400,
        )
        self.mekelle = DonationCenter.objects.create(
            name="Mekelle Center",
            city="Mekelle",
            latitude=13.4900,
            longitude=39.4700,
        )
        self.unlocated = DonationCenter.objects.create(
            name="Unknown Center", city="Nowhere"
        )

    def test_list_visible_to_any_authenticated_user(self):
        resp = self.client.get("/api/v1/donation-centers/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 3)

    def test_nearby_orders_by_distance(self):
        # Query point near Addis -> Addis first, Mekelle next, unlocated last.
        resp = self.client.get("/api/v1/donation-centers/nearby/?lat=9.0&lng=38.75")
        self.assertEqual(resp.status_code, 200, resp.content)
        names = [c["name"] for c in resp.json()]
        self.assertEqual(names[0], "Addis Center")
        self.assertEqual(names[1], "Mekelle Center")
        self.assertEqual(names[-1], "Unknown Center")
        self.assertIsNotNone(resp.json()[0]["distance_km"])

    def test_nearby_without_coords_falls_back(self):
        resp = self.client.get("/api/v1/donation-centers/nearby/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.json())
