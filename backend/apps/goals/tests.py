from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import Role

from .models import AcademicGoal

User = get_user_model()


class AcademicGoalApiTests(APITestCase):
    def setUp(self):
        student_role = Role.objects.get(name=Role.Name.STUDENT)
        supervisor_role = Role.objects.get(name=Role.Name.SUPERVISOR)
        administrator_role = Role.objects.get(name=Role.Name.ADMINISTRATOR)
        self.student = User.objects.create_user(
            email="student@example.com", name="Student", password="ComplexPass123!", role=student_role
        )
        self.other_student = User.objects.create_user(
            email="other@example.com", name="Other Student", password="ComplexPass123!", role=student_role
        )
        self.supervisor = User.objects.create_user(
            email="supervisor@example.com", name="Supervisor", password="ComplexPass123!", role=supervisor_role
        )
        self.administrator = User.objects.create_user(
            email="admin@example.com", name="Administrator", password="ComplexPass123!", role=administrator_role
        )
        self.valid_data = {
            "subject": "Data Structures",
            "description": "Master core data structures and their applications.",
            "duration": 8,
            "intensity": "Moderate",
        }

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def create_goal(self, owner=None, **changes):
        return AcademicGoal.objects.create(owner=owner or self.student, **(self.valid_data | changes))

    def test_student_can_create_goal_with_pending_status(self):
        self.authenticate(self.student)
        response = self.client.post(reverse("goal-list-create"), self.valid_data, format="json")
        goal = AcademicGoal.objects.get()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(goal.owner, self.student)
        self.assertEqual(goal.status, AcademicGoal.Status.PENDING)
        self.assertTrue(response.data["is_editable"])

    def test_unauthenticated_user_cannot_create_goal(self):
        response = self.client.post(reverse("goal-list-create"), self.valid_data, format="json")
        self.assertEqual(response.status_code, 401)

    def test_supervisor_and_administrator_cannot_create_student_goal(self):
        for user in (self.supervisor, self.administrator):
            self.authenticate(user)
            response = self.client.post(reverse("goal-list-create"), self.valid_data, format="json")
            self.assertEqual(response.status_code, 403)

    def test_required_fields_are_validated(self):
        self.authenticate(self.student)
        for field in ("subject", "description", "duration"):
            payload = self.valid_data.copy()
            payload.pop(field)
            response = self.client.post(reverse("goal-list-create"), payload, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.data)

    def test_blank_subject_and_description_are_rejected(self):
        self.authenticate(self.student)
        for field in ("subject", "description"):
            response = self.client.post(
                reverse("goal-list-create"), self.valid_data | {field: "   "}, format="json"
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.data)

    def test_duration_boundaries_are_accepted(self):
        self.authenticate(self.student)
        for duration in (1, 16):
            response = self.client.post(
                reverse("goal-list-create"), self.valid_data | {"duration": duration}, format="json"
            )
            self.assertEqual(response.status_code, 201)

    def test_invalid_duration_values_and_types_are_rejected(self):
        self.authenticate(self.student)
        for duration in (0, 17, -1, "not-a-number"):
            response = self.client.post(
                reverse("goal-list-create"), self.valid_data | {"duration": duration}, format="json"
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn("duration", response.data)

    def test_student_lists_only_own_goals(self):
        own_goal = self.create_goal()
        self.create_goal(owner=self.other_student, subject="Private goal")
        self.authenticate(self.student)
        response = self.client.get(reverse("goal-list-create"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [own_goal.pk])

    def test_student_can_retrieve_own_goal(self):
        goal = self.create_goal()
        self.authenticate(self.student)
        response = self.client.get(reverse("goal-detail", args=[goal.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], goal.pk)

    def test_another_students_goal_is_not_disclosed(self):
        goal = self.create_goal(owner=self.other_student)
        self.authenticate(self.student)
        self.assertEqual(self.client.get(reverse("goal-detail", args=[goal.pk])).status_code, 404)
        self.assertEqual(
            self.client.patch(reverse("goal-detail", args=[goal.pk]), {"subject": "Changed"}, format="json").status_code,
            404,
        )

    def test_student_can_edit_pending_goal(self):
        goal = self.create_goal()
        self.authenticate(self.student)
        response = self.client.patch(
            reverse("goal-detail", args=[goal.pk]), {"subject": "Algorithms", "duration": 10}, format="json"
        )
        goal.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(goal.subject, "Algorithms")
        self.assertEqual(goal.duration, 10)

    def test_goal_ownership_cannot_be_changed_by_request(self):
        goal = self.create_goal()
        self.authenticate(self.student)
        response = self.client.patch(
            reverse("goal-detail", args=[goal.pk]), {"owner_id": self.other_student.pk}, format="json"
        )
        goal.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(goal.owner, self.student)

    def test_non_pending_goal_cannot_be_edited(self):
        goal = self.create_goal()
        AcademicGoal.objects.filter(pk=goal.pk).update(status="plan_generated")
        self.authenticate(self.student)
        response = self.client.patch(
            reverse("goal-detail", args=[goal.pk]), {"subject": "Changed"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        goal.refresh_from_db()
        self.assertEqual(goal.subject, self.valid_data["subject"])

    def test_serializer_exposes_only_approved_goal_fields(self):
        goal = self.create_goal()
        self.authenticate(self.student)
        response = self.client.get(reverse("goal-detail", args=[goal.pk]))
        self.assertEqual(
            set(response.data),
            {"id", "subject", "description", "duration", "intensity", "status", "is_editable", "created_at", "updated_at"},
        )
        self.assertNotIn("owner", response.data)

    def test_delete_and_put_are_not_exposed(self):
        goal = self.create_goal()
        self.authenticate(self.student)
        url = reverse("goal-detail", args=[goal.pk])
        self.assertEqual(self.client.delete(url).status_code, 405)
        self.assertEqual(self.client.put(url, self.valid_data, format="json").status_code, 405)
