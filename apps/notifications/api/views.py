from notifications.models import NotificationRecord
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import NotificationRecordSerializer


class NotificationRecordViewSet(viewsets.ModelViewSet):
    queryset = NotificationRecord.objects.all().order_by("-delivered_at")
    serializer_class = NotificationRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users should only see their own notifications
        user = self.request.user
        return self.queryset.filter(user=user)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        record = self.get_object()
        record.read = True
        record.save(update_fields=["read"])
        return Response(self.get_serializer(record).data, status=status.HTTP_200_OK)
