from django.contrib import admin

from .models import DonationCenter


@admin.register(DonationCenter)
class DonationCenterAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "operating_hours", "contact_info")
    search_fields = ("name", "city")
