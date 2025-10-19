from django.contrib import admin

from .models import BloodRequest, BloodUnit

# Register your models here.
admin.site.register(BloodRequest)
admin.site.register(BloodUnit)
