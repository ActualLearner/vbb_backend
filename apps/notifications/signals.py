from django.dispatch import receiver
from django.db.models.signals import post_save
from inventory.models import BloodRequest

# We can define custom signals for more complex events if needed,
# but for now, we can use Django's built-in post_save signal.


@receiver(post_save, sender=BloodRequest)
def handle_blood_request_saved(sender, instance, created, **kwargs):
    """
    Listens for when a BloodRequest is saved and triggers notifications.
    """
    if created:
        # A new request was just created (SRS 3.2.4.3.1)
        print(f"--- NOTIFICATION TRIGGERED ---")
        print(f"  Event: New Blood Request")
        print(f"  To: Facility '{instance.fulfilling_facility.name}'")
        print(
            f"  Details: Request ID {instance.id} from '{instance.requesting_facility.name}' for {instance.units_requested} units of {instance.blood_type}."
        )
        print(f"-----------------------------")
        # In the future, you would call a function here:
        # send_push_notification(users_at_facility, message)

    else:
        # The request was updated, check if the status changed to something important
        if instance.status in [
            BloodRequest.RequestStatus.ACCEPTED,
            BloodRequest.RequestStatus.REJECTED,
        ]:
            # The request was just accepted or rejected (SRS 3.2.4.3.2)
            print(f"--- NOTIFICATION TRIGGERED ---")
            print(f"  Event: Request Status Update")
            print(f"  To: Facility '{instance.requesting_facility.name}'")
            print(
                f"  Details: Your request ID {instance.id} has been {instance.status}."
            )
            print(f"-----------------------------")
            # send_push_notification(users_at_facility, message)
