from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from inventory.models import BloodRequest, BloodUnit
from notifications.models import NotificationEvent
from tests.factories import (
    create_clinician,
    create_facility,
    create_supply,
    create_user,
)
from users.models import User


def _stock(facility, blood_type, count, days=10):
    for _ in range(count):
        BloodUnit.objects.create(
            facility=facility,
            blood_type=blood_type,
            expires_at=date.today() + timedelta(days=days),
        )


class BloodRequestAPITests(TestCase):
    def setUp(self):
        self.req_facility = create_facility(name="Requesting", woreda=1)
        self.ful_facility = create_facility(name="Fulfilling", woreda=2)
        # Requesting side is a clinician; fulfilling side is supply staff.
        self.requester = create_clinician(
            username="requester", facility=self.req_facility
        )
        self.fulfiller = create_supply(username="fulfiller", facility=self.ful_facility)

        self.client = APIClient()
        self.client.force_authenticate(self.requester)

    def _create_request(self, blood_type="A+", units=2):
        return self.client.post(
            "/api/v1/blood-requests/",
            {
                "fulfilling_facility_id": self.ful_facility.id,
                "blood_type": blood_type,
                "units_requested": units,
            },
            format="json",
        )

    def test_create_request_sets_requester_and_emits_event(self):
        _stock(self.ful_facility, "A+", 5)

        resp = self._create_request()

        self.assertEqual(resp.status_code, 201, resp.content)
        request_id = resp.json()["id"]
        created = BloodRequest.objects.get(pk=request_id)
        self.assertEqual(created.requesting_facility, self.req_facility)
        self.assertEqual(created.requested_by, self.requester)
        self.assertEqual(created.status, BloodRequest.RequestStatus.PENDING)
        # SRS 3.5.1: creation notifies the fulfilling facility.
        self.assertTrue(
            NotificationEvent.objects.filter(
                event_type="request_created", facility=self.ful_facility
            ).exists()
        )

    def test_cannot_request_from_own_facility(self):
        _stock(self.req_facility, "A+", 5)
        resp = self.client.post(
            "/api/v1/blood-requests/",
            {
                "fulfilling_facility_id": self.req_facility.id,
                "blood_type": "A+",
                "units_requested": 1,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        # Standardized error envelope (ADR-0010).
        body = resp.json()
        self.assertEqual(body["type"], "validation_error")
        self.assertEqual(body["errors"][0]["attr"], "non_field_errors")
        self.assertEqual(body["errors"][0]["code"], "invalid")

    def test_cannot_request_more_than_available(self):
        _stock(self.ful_facility, "A+", 1)
        resp = self._create_request(units=5)
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        self.assertEqual(body["type"], "validation_error")
        self.assertEqual(body["errors"][0]["code"], "invalid")
        self.assertIn("Not enough blood units", body["errors"][0]["detail"])

    def test_full_lifecycle_accept_ship_receive(self):
        _stock(self.ful_facility, "A+", 4)
        request_id = self._create_request(units=2).json()["id"]

        # Requesting facility cannot accept (SRS authorization).
        resp = self.client.post(f"/api/v1/blood-requests/{request_id}/accept/")
        self.assertEqual(resp.status_code, 403)

        # Fulfilling facility accepts: stock is deducted.
        self.client.force_authenticate(self.fulfiller)
        resp = self.client.post(f"/api/v1/blood-requests/{request_id}/accept/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()["status"], BloodRequest.RequestStatus.ACCEPTED)
        self.assertEqual(
            BloodUnit.objects.filter(
                facility=self.ful_facility, blood_type="A+"
            ).count(),
            2,
        )
        self.assertTrue(
            NotificationEvent.objects.filter(
                event_type="request_accepted", facility=self.req_facility
            ).exists()
        )

        # Fulfilling facility ships.
        resp = self.client.post(f"/api/v1/blood-requests/{request_id}/ship/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()["status"], BloodRequest.RequestStatus.IN_TRANSIT)

        # Fulfilling facility cannot receive; requesting facility can.
        resp = self.client.post(f"/api/v1/blood-requests/{request_id}/receive/")
        self.assertEqual(resp.status_code, 403)

        self.client.force_authenticate(self.requester)
        resp = self.client.post(f"/api/v1/blood-requests/{request_id}/receive/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()["status"], BloodRequest.RequestStatus.FULFILLED)
        # Units are recreated at the requesting facility (SRS 3.4.7).
        self.assertEqual(
            BloodUnit.objects.filter(
                facility=self.req_facility, blood_type="A+"
            ).count(),
            2,
        )

    def test_reject_emits_event_and_blocks_invalid_transition(self):
        _stock(self.ful_facility, "A+", 3)
        request_id = self._create_request(units=1).json()["id"]

        self.client.force_authenticate(self.fulfiller)
        resp = self.client.post(f"/api/v1/blood-requests/{request_id}/reject/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()["status"], BloodRequest.RequestStatus.REJECTED)
        self.assertTrue(
            NotificationEvent.objects.filter(
                event_type="request_rejected", facility=self.req_facility
            ).exists()
        )

        # A rejected request can no longer be shipped.
        resp = self.client.post(f"/api/v1/blood-requests/{request_id}/ship/")
        self.assertEqual(resp.status_code, 400)
        # Invalid transitions surface via the standardized envelope (ADR-0010).
        body = resp.json()
        self.assertEqual(body["type"], "validation_error")
        self.assertEqual(body["errors"][0]["code"], "invalid")

    def test_requesting_facility_can_cancel_pending(self):
        _stock(self.ful_facility, "A+", 3)
        request_id = self._create_request(units=1).json()["id"]

        resp = self.client.post(f"/api/v1/blood-requests/{request_id}/cancel/")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(resp.json()["status"], BloodRequest.RequestStatus.CANCELLED)

    def test_accept_with_insufficient_stock_rejects(self):
        # Enough at creation, but stock removed before acceptance.
        _stock(self.ful_facility, "A+", 2)
        request_id = self._create_request(units=2).json()["id"]
        BloodUnit.objects.filter(facility=self.ful_facility, blood_type="A+").delete()

        self.client.force_authenticate(self.fulfiller)
        resp = self.client.post(f"/api/v1/blood-requests/{request_id}/accept/")
        self.assertEqual(resp.status_code, 400)
        BloodRequest.objects.get(pk=request_id).refresh_from_db()
        self.assertEqual(
            BloodRequest.objects.get(pk=request_id).status,
            BloodRequest.RequestStatus.REJECTED,
        )


class InventoryAPITests(TestCase):
    def setUp(self):
        self.facility = create_facility(name="Owner", woreda=1)
        self.other = create_facility(name="Other", woreda=2)
        # Inventory is managed by supply staff.
        self.user = create_supply(username="owner", facility=self.facility)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_user_can_add_unit_to_own_facility(self):
        resp = self.client.post(
            f"/api/v1/facilities/{self.facility.id}/inventory/",
            {
                "blood_type": "O+",
                "facility_id": self.facility.id,
                "expires_at": str(date.today() + timedelta(days=20)),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(BloodUnit.objects.filter(facility=self.facility).count(), 1)

    def test_user_cannot_add_unit_to_other_facility(self):
        resp = self.client.post(
            f"/api/v1/facilities/{self.other.id}/inventory/",
            {
                "blood_type": "O+",
                "facility_id": self.other.id,
                "expires_at": str(date.today() + timedelta(days=20)),
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 403)


class DashboardAPITests(TestCase):
    def setUp(self):
        self.facility = create_facility(name="Dash", woreda=1)
        self.user = create_user(username="dash", facility=self.facility)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_dashboard_returns_summary(self):
        _stock(self.facility, "A+", 1)
        resp = self.client.get("/api/v1/dashboard/")
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertIn("inventory_summary", body)
        self.assertIn("low_stock_alerts", body)
        self.assertIn("incoming_requests_count", body)
        self.assertIn("outgoing_requests_count", body)
        self.assertIn("A+", body["low_stock_alerts"])

    def test_dashboard_requires_facility(self):
        admin = User.objects.create_user(
            username="rootadmin",
            password="password",
            role=User.Role.ADMIN,
            facility=None,
        )
        self.client.force_authenticate(admin)
        resp = self.client.get("/api/v1/dashboard/")
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        self.assertEqual(body["type"], "validation_error")
        self.assertIn("not associated with a facility", body["errors"][0]["detail"])
