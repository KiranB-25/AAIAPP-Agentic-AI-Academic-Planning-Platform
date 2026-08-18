from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStudent, IsSupervisor

from .services import student_progress_summary, supervisor_review_summary


class StudentProgressReportView(APIView):
    permission_classes = (IsStudent,)

    def get(self, request):
        return Response(student_progress_summary(student=request.user))


class SupervisorReviewReportView(APIView):
    permission_classes = (IsSupervisor,)

    def get(self, request):
        return Response(supervisor_review_summary(supervisor=request.user))
