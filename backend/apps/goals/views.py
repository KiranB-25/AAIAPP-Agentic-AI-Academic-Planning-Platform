from rest_framework import generics
from rest_framework.exceptions import ValidationError

from apps.accounts.permissions import IsStudent

from .models import AcademicGoal
from .serializers import AcademicGoalSerializer


class StudentGoalQuerysetMixin:
    permission_classes = (IsStudent,)
    serializer_class = AcademicGoalSerializer

    def get_queryset(self):
        return AcademicGoal.objects.filter(owner=self.request.user)


class AcademicGoalListCreateView(StudentGoalQuerysetMixin, generics.ListCreateAPIView):
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, status=AcademicGoal.Status.PENDING)


class AcademicGoalDetailView(StudentGoalQuerysetMixin, generics.RetrieveUpdateAPIView):
    http_method_names = ("get", "patch", "head", "options")

    def perform_update(self, serializer):
        if not serializer.instance.is_editable:
            raise ValidationError({"detail": "This goal can no longer be edited."})
        serializer.save()
