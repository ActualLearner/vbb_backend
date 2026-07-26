from django.db.models.signals import post_save
from django.dispatch import receiver

from inventory.models import BloodRequest

from .models import NotificationEvent, NotificationType

# A newly created Blood Request notifies the fulfilling facility (SRS 3.5.1).
# Status-change notifications (accepted/rejected/shipped/received, low stock)
# are emitted by the Blood Request transition seam so that an event is only
# persisted when its transaction succeeds (see ADR-0001).


@receiver(post_save, sender=BloodRequest)
def emit_blood_request_created_event(sender, instance, created, **kwargs):
    """Emit a NotificationEvent for the fulfilling facility on new requests."""
    if not created:
        return

    NotificationEvent.objects.create(
        event_type="request_created",
        notification_type=NotificationType.NEW_REQUEST,
        facility=instance.fulfilling_facility,
        payload={
            "request_id": str(instance.id),
            "requesting_facility": instance.requesting_facility.name,
            "blood_type": instance.blood_type,
            "units_requested": instance.units_requested,
            "message": (
                f"New request for {instance.units_requested} unit(s) of "
                f"{instance.blood_type} from {instance.requesting_facility.name}."
            ),
        },
    )
