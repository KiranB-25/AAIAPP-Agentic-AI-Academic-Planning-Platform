from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.accounts.models import Role
from apps.goals.models import AcademicGoal
from apps.planning.models import StudyPlan
from apps.reviews.models import PlanReview

from .models import Notification
from .services import notify_plan_ready_for_review, notify_review_submitted


User = get_user_model()


class NotificationOwnershipApiTests(APITestCase):
    def setUp(self):
        role = Role.objects.get(name=Role.Name.STUDENT)
        self.owner = User.objects.create_user(email="owner@example.com", name="Owner", password="ComplexPass123!", role=role)
        self.other_user = User.objects.create_user(email="other@example.com", name="Other", password="ComplexPass123!", role=role)
        self.notification = Notification.objects.create(
            recipient=self.owner,
            notification_type=Notification.Type.PLAN_APPROVED,
            title="Study plan approved",
            message="Your supervisor approved the plan.",
        )

    def test_only_the_recipient_can_list_or_mark_a_notification_read(self):
        self.client.force_authenticate(self.other_user)
        self.assertEqual(self.client.get("/api/notifications/").data, [])
        self.assertEqual(self.client.post(f"/api/notifications/{self.notification.id}/read/").status_code, 404)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get("/api/notifications/unread-count/").data, {"unread_count": 1})
        response = self.client.post(f"/api/notifications/{self.notification.id}/read/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data["read_at"])

    def test_plan_and_review_notifications_are_created_once_for_the_correct_recipients(self):
        supervisor_role = Role.objects.get(name=Role.Name.SUPERVISOR)
        supervisor = User.objects.create_user(
            email="supervisor@example.com", name="Supervisor", password="ComplexPass123!", role=supervisor_role,
        )
        self.owner.supervisor = supervisor
        self.owner.save()
        goal = AcademicGoal.objects.create(owner=self.owner, subject="Algorithms", description="Learn algorithms.", duration=4)
        plan = StudyPlan.objects.create(goal=goal, summary="Algorithms plan")

        notify_plan_ready_for_review(plan_id=plan.id)
        notify_plan_ready_for_review(plan_id=plan.id)
        self.assertEqual(Notification.objects.filter(recipient=supervisor, study_plan=plan).count(), 1)

        review = PlanReview.objects.create(
            study_plan=plan, supervisor=supervisor, feedback_text="Approved.", decision=PlanReview.Decision.APPROVED,
        )
        notify_review_submitted(review_id=review.id)
        notify_review_submitted(review_id=review.id)
        notifications = Notification.objects.filter(recipient=self.owner, study_plan=plan)
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications.get().notification_type, Notification.Type.PLAN_APPROVED)
