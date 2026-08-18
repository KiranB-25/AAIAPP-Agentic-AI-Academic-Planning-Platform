import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import Role
from apps.goals.models import AcademicGoal
from apps.planning.models import PlanTask, StudyPlan
from apps.planning.services.exceptions import PlanPersistenceError

User = get_user_model()


class StudentPlanApiTests(APITestCase):
    def setUp(self):
        role = Role.objects.get(name=Role.Name.STUDENT)
        self.student = User.objects.create_user(email="plan@example.com", name="Plan Student", password="ComplexPass123!", role=role)
        self.other = User.objects.create_user(email="other-plan@example.com", name="Other", password="ComplexPass123!", role=role)
        self.goal = AcademicGoal.objects.create(owner=self.student, subject="Algorithms", description="Learn algorithms.", duration=4)
        self.other_goal = AcademicGoal.objects.create(owner=self.other, subject="Private", description="Private goal.", duration=2)

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.student)

    def create_plan(self, goal=None):
        plan = StudyPlan.objects.create(goal=goal or self.goal, summary="Ordered plan")
        PlanTask.objects.create(plan=plan, week=3, title="Later", description="Later task", method="Practice")
        PlanTask.objects.create(plan=plan, week=1, title="First", description="First task", method="Recall")
        return plan

    def test_owned_retrieval_has_stable_fields_ordered_tasks_and_zero_progress(self):
        plan = self.create_plan()
        self.authenticate()
        response = self.client.get(reverse("plan-detail", args=[plan.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {"id", "goal_id", "generated_at", "summary", "status", "progress", "tasks"})
        self.assertEqual([task["week"] for task in response.data["tasks"]], [1, 3])
        self.assertEqual(response.data["tasks"][0]["objective"], "")
        self.assertFalse(response.data["tasks"][0]["revision_checkpoint"])
        self.assertEqual(response.data["progress"], 0)

    def test_cross_user_plan_and_task_access_are_hidden(self):
        plan = self.create_plan(self.other_goal)
        task = plan.tasks.first()
        self.authenticate()
        self.assertEqual(self.client.get(reverse("plan-detail", args=[plan.pk])).status_code, 404)
        self.assertEqual(self.client.patch(reverse("plan-task-detail", args=[task.pk]), {"is_completed": True}, format="json").status_code, 404)

    def test_generation_requires_owned_goal_and_is_idempotent(self):
        self.authenticate()
        url = reverse("plan-generate", args=[self.goal.pk])
        response = self.client.post(url, {"request_id": str(uuid.uuid4())}, format="json")
        self.assertEqual(response.status_code, 201)
        repeated = self.client.post(url, {"request_id": str(uuid.uuid4())}, format="json")
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(repeated.data["id"], response.data["id"])
        self.assertEqual(StudyPlan.objects.count(), 1)
        self.assertEqual(self.client.post(reverse("plan-generate", args=[self.other_goal.pk]), {"request_id": str(uuid.uuid4())}, format="json").status_code, 404)

    def test_generation_validates_request_identity_safely(self):
        self.authenticate()
        response = self.client.post(reverse("plan-generate", args=[self.goal.pk]), {"request_id": "invalid"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("traceback", str(response.data).lower())

    def test_completion_reopen_timestamp_progress_and_content_immutability(self):
        plan = self.create_plan()
        tasks = list(plan.tasks.all())
        self.authenticate()
        task_url = reverse("plan-task-detail", args=[tasks[0].pk])
        response = self.client.patch(task_url, {"is_completed": True, "title": "Tampered"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["task"]["is_completed"])
        self.assertIsNotNone(response.data["task"]["completed_at"])
        self.assertEqual(response.data["progress"], 50)
        tasks[0].refresh_from_db()
        self.assertNotEqual(tasks[0].title, "Tampered")
        self.assertEqual(self.client.get(reverse("plan-detail", args=[plan.pk])).data["progress"], 50)
        self.client.patch(reverse("plan-task-detail", args=[tasks[1].pk]), {"is_completed": True}, format="json")
        self.assertEqual(self.client.get(reverse("plan-detail", args=[plan.pk])).data["progress"], 100)
        response = self.client.patch(task_url, {"is_completed": False}, format="json")
        self.assertIsNone(response.data["task"]["completed_at"])
        self.assertEqual(response.data["progress"], 50)
        self.assertEqual(self.client.get(reverse("plan-detail", args=[plan.pk])).data["progress"], 50)

    def test_invalid_task_payload_and_unauthenticated_access_fail_safely(self):
        task = self.create_plan().tasks.first()
        self.authenticate()
        self.assertEqual(self.client.patch(reverse("plan-task-detail", args=[task.pk]), {"is_completed": "maybe"}, format="json").status_code, 400)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(reverse("plan-list")).status_code, 401)

    def test_zero_task_plan_progress_is_zero(self):
        plan = StudyPlan.objects.create(goal=self.goal, summary="Empty defensive plan")
        self.authenticate()
        self.assertEqual(self.client.get(reverse("plan-detail", args=[plan.pk])).data["progress"], 0)

    def test_generation_persistence_failure_returns_safe_error(self):
        self.authenticate()
        with patch("apps.planning.views.generation_service") as service_factory:
            service_factory.return_value.generate.side_effect = PlanPersistenceError("database details")
            response = self.client.post(
                reverse("plan-generate", args=[self.goal.pk]),
                {"request_id": str(uuid.uuid4())},
                format="json",
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data, {"detail": "The study plan could not be saved. Please try again."})
