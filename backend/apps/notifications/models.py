from django.conf import settings
from django.db import models

from apps.planning.models import StudyPlan
from apps.reviews.models import PlanReview


class Notification(models.Model):
    class Type(models.TextChoices):
        PLAN_READY_FOR_REVIEW = "plan_ready_for_review", "Plan ready for review"
        SUPERVISOR_FEEDBACK = "supervisor_feedback", "Supervisor feedback"
        REVISION_REQUIRED = "revision_required", "Revision required"
        PLAN_APPROVED = "plan_approved", "Plan approved"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=32, choices=Type.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    study_plan = models.ForeignKey(StudyPlan, null=True, blank=True, on_delete=models.CASCADE, related_name="notifications")
    review = models.ForeignKey(PlanReview, null=True, blank=True, on_delete=models.CASCADE, related_name="notifications")
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [models.UniqueConstraint(fields=("recipient", "study_plan", "notification_type"), name="unique_plan_notification_type")]
