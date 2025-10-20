from dataclasses import dataclass
from typing import List

from ..models import BloodRequest
from .authorizers import BloodRequestAuthorizer
from .lifecycle import BloodRequestLifecycleService

try:
    from notifications.models import NotificationEvent
except Exception:  # pragma: no cover - defensive import for tests
    NotificationEvent = None


@dataclass(frozen=True)
class BloodRequestTransitionResult:
    request: BloodRequest
    error: str | None = None
    remaining_units: int | None = None
    low_stock_alert: bool = False
    events: List[int] | None = None


class BloodRequestTransitionService:
    """Seam that centralizes Blood Request transition orchestration.

    Responsibilities:
    - Enforce authorization intent
    - Delegate transactional mutations to the lifecycle implementation
    - Emit domain NotificationEvent records instead of delivering notifications inline
    """

    def __init__(self, low_stock_threshold: int = 5, standard_expiry_days: int = 42):
        self.lifecycle = BloodRequestLifecycleService(
            low_stock_threshold=low_stock_threshold,
            standard_expiry_days=standard_expiry_days,
        )
        self.authorizer = BloodRequestAuthorizer()

    def _create_event(self, event_type: str, facility, payload: dict):
        if NotificationEvent is None:
            return None
        ev = NotificationEvent.objects.create(
            event_type=event_type, facility=facility, payload=payload
        )
        return ev.id

    def accept(self, user, blood_request: BloodRequest) -> BloodRequestTransitionResult:
        if not self.authorizer.can_accept_request(user, blood_request):
            return BloodRequestTransitionResult(
                request=blood_request, error="Not authorized."
            )

        result = self.lifecycle.accept(blood_request)

        events = []
        if not result.error and result.low_stock_alert:
            ev_id = self._create_event(
                "low_stock_alert",
                blood_request.fulfilling_facility,
                {
                    "blood_type": blood_request.blood_type,
                    "remaining_units": result.remaining_units,
                },
            )
            if ev_id:
                events.append(ev_id)

        return BloodRequestTransitionResult(
            request=result.request,
            error=result.error,
            remaining_units=result.remaining_units,
            low_stock_alert=result.low_stock_alert,
            events=events or None,
        )

    def ship(self, user, blood_request: BloodRequest) -> BloodRequestTransitionResult:
        if not self.authorizer.can_ship_request(user, blood_request):
            return BloodRequestTransitionResult(
                request=blood_request, error="Not authorized."
            )

        result = self.lifecycle.ship(blood_request)
        # Emit an event for status change if needed
        if not result.error:
            ev_id = self._create_event(
                "request_shipped",
                blood_request.requesting_facility,
                {"request_id": blood_request.id},
            )
            events = [ev_id] if ev_id else None
        else:
            events = None

        return BloodRequestTransitionResult(
            request=result.request,
            error=result.error,
            remaining_units=None,
            low_stock_alert=False,
            events=events,
        )

    def receive(
        self, user, blood_request: BloodRequest
    ) -> BloodRequestTransitionResult:
        if not self.authorizer.can_receive_request(user, blood_request):
            return BloodRequestTransitionResult(
                request=blood_request, error="Not authorized."
            )

        result = self.lifecycle.receive(blood_request)
        if not result.error:
            ev_id = self._create_event(
                "request_received",
                blood_request.requesting_facility,
                {"request_id": blood_request.id},
            )
            events = [ev_id] if ev_id else None
        else:
            events = None

        return BloodRequestTransitionResult(
            request=result.request,
            error=result.error,
            remaining_units=None,
            low_stock_alert=False,
            events=events,
        )

    def cancel(self, user, blood_request: BloodRequest) -> BloodRequestTransitionResult:
        if not self.authorizer.can_cancel_request(user, blood_request):
            return BloodRequestTransitionResult(
                request=blood_request, error="Not authorized."
            )

        result = self.lifecycle.cancel(blood_request)
        return BloodRequestTransitionResult(
            request=result.request,
            error=result.error,
            remaining_units=None,
            low_stock_alert=False,
            events=None,
        )

    def reject(self, user, blood_request: BloodRequest) -> BloodRequestTransitionResult:
        if not self.authorizer.can_reject_request(user, blood_request):
            return BloodRequestTransitionResult(
                request=blood_request, error="Not authorized."
            )

        result = self.lifecycle.reject(blood_request)
        return BloodRequestTransitionResult(
            request=result.request,
            error=result.error,
            remaining_units=None,
            low_stock_alert=False,
            events=None,
        )
