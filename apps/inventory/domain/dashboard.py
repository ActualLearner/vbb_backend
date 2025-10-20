from dataclasses import dataclass

from django.db.models import Count

from ..config import LOW_STOCK_THRESHOLD
from ..models import BloodRequest, BloodUnit


@dataclass(frozen=True)
class FacilityDashboardData:
    inventory_summary: list[dict]
    low_stock_alerts: list[str]
    incoming_requests_count: int
    incoming_requests_ids: list[int]
    outgoing_requests_count: int
    outgoing_requests_ids: list[int]


class FacilityDashboardService:
    def __init__(self, low_stock_threshold: int = LOW_STOCK_THRESHOLD):
        self.low_stock_threshold = low_stock_threshold

    def get_dashboard(self, facility) -> FacilityDashboardData:
        inventory_summary = list(
            BloodUnit.objects.filter(facility=facility)
            .values("blood_type")
            .annotate(total_units=Count("id"))
            .order_by("blood_type")
        )

        low_stock_alerts = [
            item["blood_type"]
            for item in inventory_summary
            if item["total_units"] <= self.low_stock_threshold
        ]

        incoming_requests_qs = BloodRequest.objects.filter(
            fulfilling_facility=facility, status=BloodRequest.RequestStatus.PENDING
        )
        incoming_requests_ids = list(incoming_requests_qs.values_list("id", flat=True))

        active_outgoing_statuses = [
            BloodRequest.RequestStatus.PENDING,
            BloodRequest.RequestStatus.ACCEPTED,
            BloodRequest.RequestStatus.IN_TRANSIT,
        ]
        outgoing_requests_qs = BloodRequest.objects.filter(
            requesting_facility=facility, status__in=active_outgoing_statuses
        )
        outgoing_requests_ids = list(outgoing_requests_qs.values_list("id", flat=True))

        return FacilityDashboardData(
            inventory_summary=inventory_summary,
            low_stock_alerts=low_stock_alerts,
            incoming_requests_count=incoming_requests_qs.count(),
            incoming_requests_ids=incoming_requests_ids,
            outgoing_requests_count=outgoing_requests_qs.count(),
            outgoing_requests_ids=outgoing_requests_ids,
        )
