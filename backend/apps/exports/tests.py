from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.accounts.models import Role
from apps.audit.models import AuditLog
from apps.goals.models import AcademicGoal
from apps.planning.models import AIExecutionLog, PlanTask, StudyPlan


User = get_user_model()


class PlanExportApiTests(APITestCase):
    def setUp(self):
        student_role = Role.objects.get(name=Role.Name.STUDENT)
        supervisor_role = Role.objects.get(name=Role.Name.SUPERVISOR)
        self.supervisor = User.objects.create_user(email="export-supervisor@example.com", name="Supervisor", password="ComplexPass123!", role=supervisor_role)
        self.student = User.objects.create_user(email="export-student@example.com", name="Student", password="ComplexPass123!", role=student_role, supervisor=self.supervisor)
        other = User.objects.create_user(email="export-other@example.com", name="Other", password="ComplexPass123!", role=student_role)
        self.plan = self._plan_for(self.student, "Owned plan")
        self.other_plan = self._plan_for(other, "Other plan")

    @staticmethod
    def _plan_for(owner, summary):
        goal = AcademicGoal.objects.create(owner=owner, subject="Algorithms", description="Learn algorithms.", duration=4)
        plan = StudyPlan.objects.create(goal=goal, summary=summary)
        PlanTask.objects.create(plan=plan, week=1, title="Read", description="Read safely.", method="Recall")
        return plan

    def test_student_export_is_pdf_audited_and_hides_ai_execution_data(self):
        AIExecutionLog.objects.create(goal=self.plan.goal, plan=self.plan, agent_name="planner", status="succeeded", system_response="private provider output")
        self.client.force_authenticate(self.student)
        response = self.client.get(f"/api/exports/plans/{self.plan.id}/")
        content = b"".join(response.streaming_content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(content.startswith(b"%PDF-"))
        self.assertNotIn(b"private provider output", content)
        self.assertTrue(AuditLog.objects.filter(actor=self.student, action=AuditLog.Action.PLAN_EXPORTED).exists())

    def test_cross_user_export_is_hidden_and_assigned_supervisor_can_export(self):
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.get(f"/api/exports/plans/{self.other_plan.id}/").status_code, 404)
        self.client.force_authenticate(self.supervisor)
        self.assertEqual(self.client.get(f"/api/exports/supervisor/plans/{self.plan.id}/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/exports/supervisor/plans/{self.other_plan.id}/").status_code, 404)
