from notifications.models import NotificationRecord
from rest_framework import serializers


class NotificationRecordSerializer(serializers.ModelSerializer):
    event_type = serializers.CharField(source="event.event_type", read_only=True)
    payload = serializers.DictField(source="event.payload", read_only=True)

    class Meta:
        model = NotificationRecord
        fields = ["id", "event", "event_type", "payload", "read", "delivered_at"]
        read_only_fields = ["id", "event", "event_type", "payload", "delivered_at"]
