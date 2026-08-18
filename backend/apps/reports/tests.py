from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.accounts.models import Role
from apps.goals.models import AcademicGoal
from apps.planning.models import PlanTask, StudyPlan


User = get_user_model()


class ReportAuthorizationTests(APITestCase):
    def setUp(self):
        student_role = Role.objects.get(name=Role.Name.STUDENT)
        supervisor_role = Role.objects.get(name=Role.Name.SUPERVISOR)
        self.supervisor = User.objects.create_user(email="report-supervisor@example.com", name="Supervisor", password="ComplexPass123!", role=supervisor_role)
        self.student = User.objects.create_user(email="report-student@example.com", name="Student", password="ComplexPass123!", role=student_role, supervisor=self.supervisor)
        goal = AcademicGoal.objects.create(owner=self.student, subject="Networks", description="Learn networks.", duration=4)
        plan = StudyPlan.objects.create(goal=goal, summary="Networks plan")
        PlanTask.objects.create(plan=plan, week=1, title="Read", description="Read safely.", method="Recall", is_completed=True)

    def test_student_progress_report_is_own_data_only(self):
        self.client.force_authenticate(self.student)
        response = self.client.get("/api/reports/student/progress/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["student_id"], self.student.id)
        self.assertEqual(response.data["plans"][0]["progress"], 100)

    def test_reports_require_the_matching_role(self):
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.get("/api/reports/supervisor/reviews/").status_code, 403)
        self.client.force_authenticate(self.supervisor)
        response = self.client.get("/api/reports/supervisor/reviews/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["assigned_students"], 1)
