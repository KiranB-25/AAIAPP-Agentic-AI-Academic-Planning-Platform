from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import Role
from apps.goals.models import AcademicGoal
from apps.planning.models import StudyPlan

from .models import PlanReview


User = get_user_model()


class SupervisorReviewApiTests(APITestCase):
    def setUp(self):
        student_role = Role.objects.get(name=Role.Name.STUDENT)
        supervisor_role = Role.objects.get(name=Role.Name.SUPERVISOR)
        self.supervisor = User.objects.create_user(
            email="assigned-supervisor@example.com", name="Assigned Supervisor",
            password="ComplexPass123!", role=supervisor_role,
        )
        self.other_supervisor = User.objects.create_user(
            email="other-supervisor@example.com", name="Other Supervisor",
            password="ComplexPass123!", role=supervisor_role,
        )
        self.student = User.objects.create_user(
            email="assigned-student@example.com", name="Assigned Student",
            password="ComplexPass123!", role=student_role, supervisor=self.supervisor,
        )
        self.other_student = User.objects.create_user(
            email="other-student@example.com", name="Other Student",
            password="ComplexPass123!", role=student_role, supervisor=self.other_supervisor,
        )
        self.plan = self._create_plan(self.student, "Assigned plan")
        self.other_plan = self._create_plan(self.other_student, "Private plan")

    @staticmethod
    def _create_plan(student, summary):
        goal = AcademicGoal.objects.create(
            owner=student, subject=summary, description="A valid academic goal.", duration=4,
        )
        return StudyPlan.objects.create(goal=goal, summary=summary)

    def test_supervisor_can_only_list_and_retrieve_assigned_student_plans(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.get("/api/reviews/supervisor/plans/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [self.plan.id])
        self.assertEqual(self.client.get(f"/api/reviews/supervisor/plans/{self.other_plan.id}/").status_code, 404)

    def test_student_cannot_access_supervisor_data(self):
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.get("/api/reviews/supervisor/plans/").status_code, 403)
        self.assertEqual(self.client.post(
            f"/api/reviews/supervisor/plans/{self.plan.id}/review/",
            {"feedback_text": "Attempt", "decision": "approved"}, format="json",
        ).status_code, 403)

    def test_final_review_updates_plan_status_and_is_immutable(self):
        self.client.force_authenticate(self.supervisor)
        url = f"/api/reviews/supervisor/plans/{self.plan.id}/review/"
        response = self.client.post(url, {"feedback_text": "Well structured.", "decision": "approved"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["decision"], PlanReview.Decision.APPROVED)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, StudyPlan.Status.APPROVED)
        self.assertEqual(PlanReview.objects.filter(study_plan=self.plan).count(), 1)
        self.assertEqual(self.client.post(
            url, {"feedback_text": "Changed", "decision": "revision_required"}, format="json",
        ).status_code, 400)

    def test_review_requires_feedback_and_a_final_decision(self):
        self.client.force_authenticate(self.supervisor)
        url = f"/api/reviews/supervisor/plans/{self.plan.id}/review/"
        self.assertEqual(self.client.post(url, {"feedback_text": "   ", "decision": "approved"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(url, {"feedback_text": "A comment", "decision": "pending"}, format="json").status_code, 400)

    def test_student_can_read_only_own_review(self):
        PlanReview.objects.create(study_plan=self.plan, supervisor=self.supervisor, feedback_text="Private feedback", decision="approved")
        PlanReview.objects.create(study_plan=self.other_plan, supervisor=self.other_supervisor, feedback_text="Other feedback", decision="approved")
        self.client.force_authenticate(self.student)
        response = self.client.get("/api/reviews/student/reviews/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["study_plan_id"] for item in response.data], [self.plan.id])
