from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.audit.services import record

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationUnreadCountView(APIView):
    def get(self, request):
        return Response({"unread_count": Notification.objects.filter(recipient=request.user, read_at__isnull=True).count()})


class NotificationMarkReadView(APIView):
    def post(self, request, pk):
        notification = Notification.objects.filter(recipient=request.user, pk=pk).first()
        if notification is None:
            from rest_framework.exceptions import NotFound
            raise NotFound("Notification not found.")
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=("read_at",))
            record(
                actor=request.user,
                action=AuditLog.Action.NOTIFICATION_READ,
                description=f"Marked notification #{notification.pk} as read.",
                request=request,
            )
        return Response(NotificationSerializer(notification).data)
