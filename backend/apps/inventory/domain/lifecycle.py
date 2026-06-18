from dataclasses import dataclass
from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from ..config import LOW_STOCK_THRESHOLD, STANDARD_EXPIRY_DAYS
from ..models import BloodRequest, BloodUnit


@dataclass(frozen=True)
class BloodRequestLifecycleResult:
    request: BloodRequest
    error: str | None = None
    remaining_units: int | None = None
    low_stock_alert: bool = False


class BloodRequestLifecycleService:
    def __init__(
        self,
        low_stock_threshold: int = LOW_STOCK_THRESHOLD,
        standard_expiry_days: int = STANDARD_EXPIRY_DAYS,
    ):
        self.low_stock_threshold = low_stock_threshold
        self.standard_expiry_days = standard_expiry_days

    def _new_expiry(self) -> date:
        return date.today() + timedelta(days=self.standard_expiry_days)

    def accept(self, blood_request: BloodRequest) -> BloodRequestLifecycleResult:
        if blood_request.status != BloodRequest.RequestStatus.PENDING:
            return BloodRequestLifecycleResult(
                request=blood_request,
                error="Request is not in PENDING state.",
            )

        with transaction.atomic():
            available_units = BloodUnit.objects.select_for_update().filter(
                facility=blood_request.fulfilling_facility,
                blood_type=blood_request.blood_type,
            )

            if available_units.count() < blood_request.units_requested:
                blood_request.status = BloodRequest.RequestStatus.REJECTED
                blood_request.rejection_reason = "Insufficient stock at acceptance."
                blood_request.save(
                    update_fields=["status", "rejection_reason", "updated_at"]
                )
                return BloodRequestLifecycleResult(
                    request=blood_request,
                    error=(
                        "Insufficient stock to accept this request. "
                        "Request has been rejected."
                    ),
                )

            units_to_remove = available_units.order_by("expires_at")[
                : blood_request.units_requested
            ]
            BloodUnit.objects.filter(
                pk__in=[unit.pk for unit in units_to_remove]
            ).delete()

            blood_request.status = BloodRequest.RequestStatus.ACCEPTED
            blood_request.acceptance_timestamp = timezone.now()
            blood_request.save(
                update_fields=["status", "acceptance_timestamp", "updated_at"]
            )

            remaining_units = BloodUnit.objects.filter(
                facility=blood_request.fulfilling_facility,
                blood_type=blood_request.blood_type,
            ).count()

            return BloodRequestLifecycleResult(
                request=blood_request,
                remaining_units=remaining_units,
                low_stock_alert=remaining_units <= self.low_stock_threshold,
            )

    def ship(self, blood_request: BloodRequest) -> BloodRequestLifecycleResult:
        if blood_request.status != BloodRequest.RequestStatus.ACCEPTED:
            return BloodRequestLifecycleResult(
                request=blood_request,
                error="Request must be ACCEPTED before shipping.",
            )

        blood_request.status = BloodRequest.RequestStatus.IN_TRANSIT
        blood_request.dispatch_timestamp = timezone.now()
        blood_request.save(update_fields=["status", "dispatch_timestamp", "updated_at"])
        return BloodRequestLifecycleResult(request=blood_request)

    def receive(self, blood_request: BloodRequest) -> BloodRequestLifecycleResult:
        if blood_request.status != BloodRequest.RequestStatus.IN_TRANSIT:
            return BloodRequestLifecycleResult(
                request=blood_request,
                error="Request is not IN_TRANSIT.",
            )

        with transaction.atomic():
            new_units = [
                BloodUnit(
                    facility=blood_request.requesting_facility,
                    blood_type=blood_request.blood_type,
                    expires_at=self._new_expiry(),
                )
                for _ in range(blood_request.units_requested)
            ]
            BloodUnit.objects.bulk_create(new_units)

            blood_request.status = BloodRequest.RequestStatus.FULFILLED
            blood_request.fulfillment_timestamp = timezone.now()
            blood_request.save(
                update_fields=["status", "fulfillment_timestamp", "updated_at"]
            )

        return BloodRequestLifecycleResult(request=blood_request)

    def cancel(self, blood_request: BloodRequest) -> BloodRequestLifecycleResult:
        # A request may be cancelled while PENDING or ACCEPTED (SDS 4.6). When an
        # accepted request is cancelled, the reserved stock is returned to the
        # fulfilling facility so it is not silently lost.
        if blood_request.status not in (
            BloodRequest.RequestStatus.PENDING,
            BloodRequest.RequestStatus.ACCEPTED,
        ):
            return BloodRequestLifecycleResult(
                request=blood_request,
                error="Only PENDING or ACCEPTED requests can be cancelled.",
            )

        with transaction.atomic():
            if blood_request.status == BloodRequest.RequestStatus.ACCEPTED:
                restored = [
                    BloodUnit(
                        facility=blood_request.fulfilling_facility,
                        blood_type=blood_request.blood_type,
                        expires_at=self._new_expiry(),
                    )
                    for _ in range(blood_request.units_requested)
                ]
                BloodUnit.objects.bulk_create(restored)

            blood_request.status = BloodRequest.RequestStatus.CANCELLED
            blood_request.save(update_fields=["status", "updated_at"])
        return BloodRequestLifecycleResult(request=blood_request)

    def reject(self, blood_request: BloodRequest) -> BloodRequestLifecycleResult:
        if blood_request.status != BloodRequest.RequestStatus.PENDING:
            return BloodRequestLifecycleResult(
                request=blood_request,
                error="Only PENDING requests can be rejected.",
            )

        blood_request.status = BloodRequest.RequestStatus.REJECTED
        blood_request.save(update_fields=["status", "updated_at"])
        return BloodRequestLifecycleResult(request=blood_request)
