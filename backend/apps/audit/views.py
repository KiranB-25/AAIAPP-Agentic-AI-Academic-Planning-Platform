from rest_framework import generics

from apps.accounts.permissions import IsAdministrator

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(generics.ListAPIView):
    permission_classes = (IsAdministrator,)
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related("actor")
