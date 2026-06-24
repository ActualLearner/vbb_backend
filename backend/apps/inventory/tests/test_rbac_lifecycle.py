from datetime import date, timedelta

from audit.models import AuditLog
from django.test import TestCase
from inventory.models import BloodRequest, BloodUnit
from rest_framework.test import APIClient

from tests.factories import (
    create_admin,
    create_clinician,
    create_facility,
    create_supply,
)


def _stock(facility, blood_type, count, days=10):
    for _ in range(count):
        BloodUnit.objects.create(
            facility=facility,
            blood_type=blood_type,
            expires_at=date.today() + timedelta(days=days),
        )


class RBACMatrixTests(TestCase):
    def setUp(self):
        self.req = create_facility(name="Req", woreda=1)
        self.ful = create_facility(name="Ful", woreda=2)
        self.clinician = create_clinician(username="clin", facility=self.req)
        self.supply = create_supply(username="sup", facility=self.ful)
        self.req_supply = create_supply(username="reqsup", facility=self.req)
        self.ful_clinician = create_clinician(username="fulclin", facility=self.ful)
        self.admin = create_admin(username="admin", facility=self.req)
        self.client = APIClient()

    def _make_request(self):
        _stock(self.ful, "A+", 3)
        self.client.force_authenticate(self.clinician)
        return self.client.post(
            "/api/v1/blood-requests/",
            {
                "fulfilling_facility_id": str(self.ful.id),
                "blood_type": "A+",
                "units_requested": 1,
            },
            format="json",
        ).json()["id"]

    def test_admin_cannot_create_request(self):
        _stock(self.ful, "A+", 3)
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            "/api/v1/blood-requests/",
            {
                "fulfilling_facility_id": str(self.ful.id),
                "blood_type": "A+",
                "units_requested": 1,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_admin_cannot_accept_request(self):
        rid = self._make_request()
        self.client.force_authenticate(
            create_admin(username="fadmin", facility=self.ful)
        )
        resp = self.client.post(f"/api/v1/blood-requests/{rid}/accept/")
        self.assertEqual(resp.status_code, 403)

    def test_admin_cannot_add_inventory(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            f"/api/v1/facilities/{self.req.id}/inventory/",
            {
                "blood_type": "O+",
                "facility_id": str(self.req.id),
                "expires_at": str(date.today() + timedelta(days=20)),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_supply_cannot_create_request(self):
        _stock(self.ful, "A+", 3)
        self.client.force_authenticate(self.req_supply)
        resp = self.client.post(
            "/api/v1/blood-requests/",
            {
                "fulfilling_facility_id": str(self.ful.id),
                "blood_type": "A+",
                "units_requested": 1,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_clinician_cannot_add_inventory(self):
        self.client.force_authenticate(self.clinician)
        resp = self.client.post(
            f"/api/v1/facilities/{self.req.id}/inventory/",
            {
                "blood_type": "O+",
                "facility_id": str(self.req.id),
                "expires_at": str(date.today() + timedelta(days=20)),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_clinician_cannot_accept_request(self):
        rid = self._make_request()
        self.client.force_authenticate(self.ful_clinician)
        resp = self.client.post(f"/api/v1/blood-requests/{rid}/accept/")
        self.assertEqual(resp.status_code, 403)


class LifecycleExtrasTests(TestCase):
    def setUp(self):
        self.req = create_facility(name="Req", woreda=1)
        self.ful = create_facility(name="Ful", woreda=2)
        self.pro = create_clinician(username="clin", facility=self.req)
        self.ful_pro = create_supply(username="sup", facility=self.ful)
        self.client = APIClient()
        self.client.force_authenticate(self.pro)

    def _create(self, units=2, notes="urgent"):
        _stock(self.ful, "A+", 4)
        return self.client.post(
            "/api/v1/blood-requests/",
            {
                "fulfilling_facility_id": str(self.ful.id),
                "blood_type": "A+",
                "units_requested": units,
                "notes": notes,
            },
            format="json",
        ).json()["id"]

    def test_notes_persisted(self):
        rid = self._create(notes="please hurry")
        self.assertEqual(BloodRequest.objects.get(pk=rid).notes, "please hurry")

    def test_reject_with_reason(self):
        rid = self._create(units=1)
        self.client.force_authenticate(self.ful_pro)
        resp = self.client.post(
            f"/api/v1/blood-requests/{rid}/reject/",
            {"reason": "quarantined stock"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(
            BloodRequest.objects.get(pk=rid).rejection_reason, "quarantined stock"
        )

    def test_cancel_from_accepted_restores_stock(self):
        rid = self._create(units=2)
        self.client.force_authenticate(self.ful_pro)
        self.client.post(f"/api/v1/blood-requests/{rid}/accept/")
        # After accept, fulfilling stock dropped from 4 to 2.
        self.assertEqual(
            BloodUnit.objects.filter(facility=self.ful, blood_type="A+").count(), 2
        )
        # Requesting clinician cancels the accepted request.
        self.client.force_authenticate(self.pro)
        resp = self.client.post(f"/api/v1/blood-requests/{rid}/cancel/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()["status"], BloodRequest.RequestStatus.CANCELLED)
        # Restored back to 4.
        self.assertEqual(
            BloodUnit.objects.filter(facility=self.ful, blood_type="A+").count(), 4
        )

    def test_timestamps_and_status_history(self):
        rid = self._create(units=1)
        self.client.force_authenticate(self.ful_pro)
        self.client.post(f"/api/v1/blood-requests/{rid}/accept/")
        self.client.post(f"/api/v1/blood-requests/{rid}/ship/")
        self.client.force_authenticate(self.pro)
        resp = self.client.post(f"/api/v1/blood-requests/{rid}/receive/")
        body = resp.json()
        self.assertIsNotNone(body["acceptance_timestamp"])
        self.assertIsNotNone(body["dispatch_timestamp"])
        self.assertIsNotNone(body["fulfillment_timestamp"])
        # Status history records accept, ship, receive transitions.
        statuses = [e["to_status"] for e in body["status_events"]]
        self.assertEqual(
            statuses,
            [
                BloodRequest.RequestStatus.ACCEPTED,
                BloodRequest.RequestStatus.IN_TRANSIT,
                BloodRequest.RequestStatus.FULFILLED,
            ],
        )

    def test_transition_writes_audit_entry(self):
        rid = self._create(units=1)
        self.client.force_authenticate(self.ful_pro)
        self.client.post(f"/api/v1/blood-requests/{rid}/accept/")
        self.assertTrue(
            AuditLog.objects.filter(
                action="blood_request.accept", target_id=str(rid)
            ).exists()
        )


class DistrictAndExpiryTests(TestCase):
    def setUp(self):
        self.facility = create_facility(name="A Hospital", woreda=7)
        self.sibling = create_facility(name="B Hospital", woreda=7)
        self.outsider = create_facility(name="Far Hospital", woreda=9)
        self.user = create_clinician(username="u", facility=self.facility)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_district_inventory_scopes_to_woreda(self):
        _stock(self.facility, "A+", 2)
        _stock(self.sibling, "B+", 1)
        _stock(self.outsider, "O+", 5)
        resp = self.client.get("/api/v1/district-inventory/")
        self.assertEqual(resp.status_code, 200, resp.content)
        names = {row["facility_name"] for row in resp.json()}
        self.assertEqual(names, {"A Hospital", "B Hospital"})

    def test_district_inventory_search(self):
        _stock(self.facility, "A+", 2)
        _stock(self.sibling, "B+", 1)
        resp = self.client.get("/api/v1/district-inventory/?search=B Hospital")
        names = {row["facility_name"] for row in resp.json()}
        self.assertEqual(names, {"B Hospital"})

    def test_expiring_soon_flag(self):
        BloodUnit.objects.create(
            facility=self.facility,
            blood_type="A+",
            expires_at=date.today() + timedelta(days=3),
        )
        resp = self.client.get(f"/api/v1/facilities/{self.facility.id}/inventory/")
        unit = resp.json()["results"][0]
        self.assertTrue(unit["is_expiring_soon"])
        self.assertFalse(unit["is_expired"])
