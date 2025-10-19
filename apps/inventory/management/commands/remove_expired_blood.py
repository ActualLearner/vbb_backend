from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.inventory.models import BloodUnit


class Command(BaseCommand):
    """
    A Django management command to find and remove expired blood units from the database.
    Fulfills the data integrity requirement to not show expired inventory.
    """

    help = "Removes all blood units that have passed their expiration date."

    def handle(self, *args, **options):
        """
        The main logic of the command.
        """
        today = timezone.now().date()
        self.stdout.write(
            f"Checking for blood units that expired on or before {today}..."
        )

        # Find all blood units where the 'expires_at' date is in the past.
        expired_units = BloodUnit.objects.filter(expires_at__lt=today)
        count = expired_units.count()

        if count > 0:
            # If we found expired units, delete them.
            # The delete() method returns a dictionary with the count of deleted objects.
            deleted_info = expired_units.delete()
            deleted_count = deleted_info[0]  # The count is the first element

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully removed {deleted_count} expired blood unit(s)."
                )
            )
        else:
            # If no expired units were found, report that.
            self.stdout.write(
                self.style.SUCCESS("No expired blood units found. Inventory is clean.")
            )
