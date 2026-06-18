from dataclasses import dataclass
from typing import List

from ..models import BloodRequest, BloodRequestStatusEvent
from .authorizers import BloodRequestAuthorizer
from .lifecycle import BloodRequestLifecycleService

try:
    from notifications.models import NotificationEvent, NotificationType
except Exception:  # pragma: no cover - defensive import for tests
    NotificationEvent = None
    NotificationType = None

try:
    from audit.services import record_audit
except Exception:  # pragma: no cover - defensive

    def record_audit(*args, **kwargs):
        return None


@dataclass(frozen=True)
class BloodRequestTransitionResult:
    request: BloodRequest
    error: str | None = None
    remaining_units: int | None = None
    low_stock_alert: bool = False
    events: List[str] | None = None


class BloodRequestTransitionService:
    """Seam that centralizes Blood Request transition orchestration.

    Responsibilities:
    - Enforce authorization intent
    - Delegate transactional mutations to the lifecycle implementation
    - Record status history, emit domain NotificationEvent records, and write
      audit entries (delivery of notifications is handled asynchronously).
    """

    def __init__(self, low_stock_threshold: int = 5, standard_expiry_days: int = 42):
        self.lifecycle = BloodRequestLifecycleService(
            low_stock_threshold=low_stock_threshold,
            standard_expiry_days=standard_expiry_days,
        )
        self.authorizer = BloodRequestAuthorizer()

    def _create_event(self, notification_type, facility, payload: dict):
        if NotificationEvent is None:
            return None
        ev = NotificationEvent.objects.create(
            event_type=str(notification_type).lower(),
            notification_type=notification_type,
            facility=facility,
            payload=payload,
        )
        return str(ev.id)

    def _record_history(self, blood_request, from_status, user):
        BloodRequestStatusEvent.objects.create(
            request=blood_request,
            from_status=from_status,
            to_status=blood_request.status,
            actor=user if getattr(user, "is_authenticated", False) else None,
        )

    def accept(self, user, blood_request: BloodRequest) -> BloodRequestTransitionResult:
        if not self.authorizer.can_accept_request(user, blood_request):
            return BloodRequestTransitionResult(
                request=blood_request, error="Not authorized."
            )

        from_status = blood_request.status
        result = self.lifecycle.accept(blood_request)

        events = []
        if not result.error:
            self._record_history(blood_request, from_status, user)
            record_audit(
                user,
                "blood_request.accept",
                target=blood_request,
                metadata={"units": blood_request.units_requested},
            )
            ev_id = self._create_event(
                NotificationType.REQUEST_ACCEPTED,
                blood_request.requesting_facility,
                {
                    "request_id": str(blood_request.id),
                    "blood_type": blood_request.blood_type,
                    "message": f"Request {blood_request.id} was accepted.",
                },
            )
            if ev_id:
                events.append(ev_id)

            if result.low_stock_alert:
                ev_id = self._create_event(
                    NotificationType.LOW_STOCK,
                    blood_request.fulfilling_facility,
                    {
                        "blood_type": blood_request.blood_type,
                        "remaining_units": result.remaining_units,
                        "message": (
                            f"Low stock for {blood_request.blood_type}: "
                            f"{result.remaining_units} unit(s) remaining."
                        ),
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

        from_status = blood_request.status
        result = self.lifecycle.ship(blood_request)
        events = None
        if not result.error:
            self._record_history(blood_request, from_status, user)
            record_audit(user, "blood_request.ship", target=blood_request)
            ev_id = self._create_event(
                NotificationType.REQUEST_IN_TRANSIT,
                blood_request.requesting_facility,
                {
                    "request_id": str(blood_request.id),
                    "message": f"Request {blood_request.id} is in transit.",
                },
            )
            events = [ev_id] if ev_id else None

        return BloodRequestTransitionResult(
            request=result.request,
            error=result.error,
            events=events,
        )

    def receive(
        self, user, blood_request: BloodRequest
    ) -> BloodRequestTransitionResult:
        if not self.authorizer.can_receive_request(user, blood_request):
            return BloodRequestTransitionResult(
                request=blood_request, error="Not authorized."
            )

        from_status = blood_request.status
        result = self.lifecycle.receive(blood_request)
        events = None
        if not result.error:
            self._record_history(blood_request, from_status, user)
            record_audit(user, "blood_request.receive", target=blood_request)
            ev_id = self._create_event(
                NotificationType.REQUEST_FULFILLED,
                blood_request.fulfilling_facility,
                {
                    "request_id": str(blood_request.id),
                    "message": f"Request {blood_request.id} was received.",
                },
            )
            events = [ev_id] if ev_id else None

        return BloodRequestTransitionResult(
            request=result.request,
            error=result.error,
            events=events,
        )

    def cancel(self, user, blood_request: BloodRequest) -> BloodRequestTransitionResult:
        if not self.authorizer.can_cancel_request(user, blood_request):
            return BloodRequestTransitionResult(
                request=blood_request, error="Not authorized."
            )

        from_status = blood_request.status
        result = self.lifecycle.cancel(blood_request)
        events = None
        if not result.error:
            self._record_history(blood_request, from_status, user)
            record_audit(user, "blood_request.cancel", target=blood_request)
            ev_id = self._create_event(
                NotificationType.REQUEST_CANCELLED,
                blood_request.fulfilling_facility,
                {
                    "request_id": str(blood_request.id),
                    "message": f"Request {blood_request.id} was cancelled.",
                },
            )
            events = [ev_id] if ev_id else None

        return BloodRequestTransitionResult(
            request=result.request,
            error=result.error,
            events=events,
        )

    def reject(
        self, user, blood_request: BloodRequest, reason: str = ""
    ) -> BloodRequestTransitionResult:
        if not self.authorizer.can_reject_request(user, blood_request):
            return BloodRequestTransitionResult(
                request=blood_request, error="Not authorized."
            )

        from_status = blood_request.status
        result = self.lifecycle.reject(blood_request)
        events = None
        if not result.error:
            if reason:
                blood_request.rejection_reason = reason
                blood_request.save(update_fields=["rejection_reason"])
            self._record_history(blood_request, from_status, user)
            record_audit(
                user,
                "blood_request.reject",
                target=blood_request,
                metadata={"reason": reason},
            )
            ev_id = self._create_event(
                NotificationType.REQUEST_REJECTED,
                blood_request.requesting_facility,
                {
                    "request_id": str(blood_request.id),
                    "blood_type": blood_request.blood_type,
                    "reason": reason,
                    "message": f"Request {blood_request.id} was rejected.",
                },
            )
            events = [ev_id] if ev_id else None

        return BloodRequestTransitionResult(
            request=result.request,
            error=result.error,
            events=events,
        )
