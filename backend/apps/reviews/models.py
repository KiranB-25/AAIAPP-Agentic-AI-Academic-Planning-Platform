from django.conf import settings
from django.db import models

from apps.planning.models import StudyPlan


class PlanReview(models.Model):
    class Decision(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REVISION_REQUIRED = "revision_required", "Revision Required"

    study_plan = models.OneToOneField(StudyPlan, on_delete=models.CASCADE, related_name="review")
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="plan_reviews")
    feedback_text = models.TextField()
    decision = models.CharField(max_length=32, choices=Decision.choices, default=Decision.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
