from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class AcademicGoal(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PLAN_GENERATED = "plan_generated", "Plan Generated"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="academic_goals",
    )
    subject = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(16)],
        help_text="Duration in weeks (1–16).",
    )
    intensity = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")

    @property
    def is_editable(self) -> bool:
        return self.status == self.Status.PENDING

    def __str__(self) -> str:
        return self.subject
