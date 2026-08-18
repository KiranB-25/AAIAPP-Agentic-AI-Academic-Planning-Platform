from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from apps.accounts.permissions import IsStudent, IsSupervisor
from apps.audit.models import AuditLog
from apps.audit.services import record
from apps.planning.models import StudyPlan

from .services import study_plan_pdf


class PlanExportView(APIView):
    permission_classes = (IsStudent,)

    def get(self, request, pk):
        plan = get_object_or_404(StudyPlan.objects.filter(goal__owner=request.user).select_related("goal").prefetch_related("tasks"), pk=pk)
        record(actor=request.user, action=AuditLog.Action.PLAN_EXPORTED, description=f"Exported own study plan #{plan.pk} as PDF.", request=request)
        return FileResponse(iter([study_plan_pdf(plan)]), as_attachment=True, filename=f"study-plan-{plan.pk}.pdf", content_type="application/pdf")


class SupervisorPlanExportView(APIView):
    permission_classes = (IsSupervisor,)

    def get(self, request, pk):
        plan = get_object_or_404(StudyPlan.objects.filter(goal__owner__supervisor=request.user).select_related("goal").prefetch_related("tasks"), pk=pk)
        record(actor=request.user, action=AuditLog.Action.PLAN_EXPORTED, description=f"Exported assigned study plan #{plan.pk} as PDF.", request=request)
        return FileResponse(iter([study_plan_pdf(plan)]), as_attachment=True, filename=f"study-plan-{plan.pk}.pdf", content_type="application/pdf")
