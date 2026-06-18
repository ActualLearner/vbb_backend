from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from inventory.domain.authorizers import BloodRequestAuthorizer
from inventory.domain.dashboard import FacilityDashboardService
from inventory.domain.lifecycle import BloodRequestLifecycleService
from inventory.models import BloodRequest, BloodUnit
from users.models import Facility

User = get_user_model()


class BloodRequestLifecycleServiceTests(TestCase):
    def setUp(self):
        self.requesting_facility = Facility.objects.create(
            name="Requesting Facility",
            region="Region A",
            zone="Zone 1",
            woreda=1,
        )
        self.fulfilling_facility = Facility.objects.create(
            name="Fulfilling Facility",
            region="Region B",
            zone="Zone 2",
            woreda=2,
        )
        self.requested_by = User.objects.create_user(
            username="requester",
            password="password123",
            role=User.Role.PROFESSIONAL,
            facility=self.requesting_facility,
        )

    def test_accepts_request_by_deducting_oldest_units_first(self):
        oldest_unit = BloodUnit.objects.create(
            facility=self.fulfilling_facility,
            blood_type="A+",
            expires_at=date.today() + timedelta(days=3),
        )
        newer_unit = BloodUnit.objects.create(
            facility=self.fulfilling_facility,
            blood_type="A+",
            expires_at=date.today() + timedelta(days=10),
        )
        BloodUnit.objects.create(
            facility=self.fulfilling_facility,
            blood_type="A+",
            expires_at=date.today() + timedelta(days=20),
        )
        blood_request = BloodRequest.objects.create(
            requesting_facility=self.requesting_facility,
            fulfilling_facility=self.fulfilling_facility,
            requested_by=self.requested_by,
            blood_type="A+",
            units_requested=2,
        )

        result = BloodRequestLifecycleService(low_stock_threshold=5).accept(
            blood_request
        )

        blood_request.refresh_from_db()
        self.assertIsNone(result.error)
        self.assertEqual(blood_request.status, BloodRequest.RequestStatus.ACCEPTED)
        self.assertEqual(result.remaining_units, 1)
        self.assertTrue(result.low_stock_alert)
        self.assertFalse(
            BloodUnit.objects.filter(
                pk=oldest_unit.pk, facility=self.fulfilling_facility
            ).exists()
        )
        self.assertFalse(
            BloodUnit.objects.filter(
                pk=newer_unit.pk, facility=self.fulfilling_facility
            ).exists()
        )


class FacilityDashboardServiceTests(TestCase):
    def setUp(self):
        self.facility = Facility.objects.create(
            name="Dashboard Facility",
            region="Region A",
            zone="Zone 1",
            woreda=3,
        )
        self.other_facility = Facility.objects.create(
            name="Other Facility",
            region="Region B",
            zone="Zone 2",
            woreda=4,
        )
        self.other_user = User.objects.create_user(
            username="other-dashboard-user",
            password="password123",
            role=User.Role.PROFESSIONAL,
            facility=self.other_facility,
        )
        self.user = User.objects.create_user(
            username="dashboard-user",
            password="password123",
            role=User.Role.PROFESSIONAL,
            facility=self.facility,
        )

    def test_collects_facility_summary_requests_and_low_stock_alerts(self):
        BloodUnit.objects.create(
            facility=self.facility,
            blood_type="A+",
            expires_at=date.today() + timedelta(days=10),
        )
        BloodUnit.objects.create(
            facility=self.facility,
            blood_type="B+",
            expires_at=date.today() + timedelta(days=10),
        )
        BloodUnit.objects.create(
            facility=self.facility,
            blood_type="B+",
            expires_at=date.today() + timedelta(days=11),
        )
        incoming_request = BloodRequest.objects.create(
            requesting_facility=self.other_facility,
            fulfilling_facility=self.facility,
            requested_by=self.other_user,
            blood_type="A+",
            units_requested=1,
        )
        outgoing_pending = BloodRequest.objects.create(
            requesting_facility=self.facility,
            fulfilling_facility=self.other_facility,
            requested_by=self.user,
            blood_type="B+",
            units_requested=1,
        )
        BloodRequest.objects.create(
            requesting_facility=self.facility,
            fulfilling_facility=self.other_facility,
            requested_by=self.user,
            blood_type="B+",
            units_requested=1,
            status=BloodRequest.RequestStatus.FULFILLED,
        )

        summary = FacilityDashboardService(low_stock_threshold=1).get_dashboard(
            self.facility
        )

        self.assertEqual(
            summary.inventory_summary,
            [
                {"blood_type": "A+", "total_units": 1},
                {"blood_type": "B+", "total_units": 2},
            ],
        )
        self.assertEqual(summary.low_stock_alerts, ["A+"])
        self.assertEqual(summary.incoming_requests_count, 1)
        self.assertEqual(summary.incoming_requests_ids, [str(incoming_request.id)])
        self.assertEqual(summary.outgoing_requests_count, 1)
        self.assertEqual(summary.outgoing_requests_ids, [str(outgoing_pending.id)])


class BloodRequestAuthorizerTests(TestCase):
    def setUp(self):
        self.requesting_facility = Facility.objects.create(
            name="Requesting Facility",
            region="Region A",
            zone="Zone 1",
            woreda=5,
        )
        self.fulfilling_facility = Facility.objects.create(
            name="Fulfilling Facility",
            region="Region B",
            zone="Zone 2",
            woreda=6,
        )
        self.requesting_user = User.objects.create_user(
            username="requesting-user",
            password="password123",
            role=User.Role.PROFESSIONAL,
            facility=self.requesting_facility,
        )
        self.fulfilling_user = User.objects.create_user(
            username="fulfilling-user",
            password="password123",
            role=User.Role.PROFESSIONAL,
            facility=self.fulfilling_facility,
        )
        self.admin_user = User.objects.create_user(
            username="admin-user",
            password="password123",
            role=User.Role.ADMIN,
            facility=None,
        )
        self.blood_request = BloodRequest.objects.create(
            requesting_facility=self.requesting_facility,
            fulfilling_facility=self.fulfilling_facility,
            requested_by=self.requesting_user,
            blood_type="O+",
            units_requested=1,
        )

    def test_distinguishes_requesting_and_fulfilling_facility_actions(self):
        authorizer = BloodRequestAuthorizer()

        self.assertTrue(
            authorizer.can_accept_request(self.fulfilling_user, self.blood_request)
        )
        self.assertFalse(
            authorizer.can_accept_request(self.requesting_user, self.blood_request)
        )
        self.assertTrue(
            authorizer.can_receive_request(self.requesting_user, self.blood_request)
        )
        self.assertFalse(
            authorizer.can_receive_request(self.fulfilling_user, self.blood_request)
        )
        # SDS 2.3.2: administrators perform no clinical actions.
        self.assertFalse(
            authorizer.can_cancel_request(self.admin_user, self.blood_request)
        )
        self.assertFalse(
            authorizer.can_accept_request(self.admin_user, self.blood_request)
        )
        # The requesting facility's professional may cancel their own request.
        self.assertTrue(
            authorizer.can_cancel_request(self.requesting_user, self.blood_request)
        )


"""Tests are currently sourced from inventory/tests.py.

This file exists to reserve the new package structure without duplicating test runs.
"""
