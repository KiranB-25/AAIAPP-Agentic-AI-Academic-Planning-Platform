import uuid

from django.db import models

from apps.goals.models import AcademicGoal


class StudyPlan(models.Model):
    class Status(models.TextChoices):
        GENERATED = "generated", "Generated"
        APPROVED = "approved", "Approved"
        REVISION_REQUIRED = "revision_required", "Revision Required"

    goal = models.OneToOneField(AcademicGoal, on_delete=models.CASCADE, related_name="study_plan")
    generated_at = models.DateTimeField(auto_now_add=True)
    summary = models.TextField()
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.GENERATED)

    class Meta:
        ordering = ("-generated_at", "-id")

    def __str__(self) -> str:
        return f"Study plan for {self.goal.subject}"


class PlanTask(models.Model):
    plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name="tasks")
    week = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    method = models.CharField(max_length=255)
    objective = models.TextField(blank=True, default="")
    revision_checkpoint = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("week", "id")
        constraints = [
            models.UniqueConstraint(fields=("plan", "week", "title"), name="unique_plan_week_task_title"),
        ]

    def __str__(self) -> str:
        return self.title


class ImmutableAIExecutionLogQuerySet(models.QuerySet):
    def bulk_create(self, objs, **kwargs):
        for obj in objs:
            obj._prepare_traceability()
        return super().bulk_create(objs, **kwargs)

    def update(self, **kwargs):
        raise TypeError("AI execution logs are immutable.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise TypeError("AI execution logs are immutable.")

    def delete(self):
        raise TypeError("AI execution logs are immutable.")


class AIExecutionLog(models.Model):
    class AgentName(models.TextChoices):
        ORCHESTRATOR = "orchestrator", "Agent Orchestrator"
        PLANNER = "planner", "Planner Agent"
        CONTENT_GENERATOR = "content_generator", "Content Generator Agent"
        EVALUATION = "evaluation", "Evaluation Agent"
        AGGREGATOR = "aggregator", "Plan Aggregator"

    class Status(models.TextChoices):
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    execution_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    request_id = models.UUIDField(default=uuid.uuid4, db_index=True, editable=False)
    goal = models.ForeignKey(
        AcademicGoal,
        on_delete=models.PROTECT,
        related_name="ai_execution_logs",
        null=True,
        blank=True,
    )
    plan = models.ForeignKey(
        StudyPlan,
        on_delete=models.PROTECT,
        related_name="execution_logs",
        null=True,
        blank=True,
    )
    agent_name = models.CharField(max_length=32, choices=AgentName.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, choices=Status.choices)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    system_response = models.TextField(blank=True)
    token_usage = models.PositiveIntegerField(null=True, blank=True)

    objects = ImmutableAIExecutionLogQuerySet.as_manager()

    class Meta:
        ordering = ("timestamp", "id")
        base_manager_name = "objects"
        default_manager_name = "objects"
        constraints = [
            models.UniqueConstraint(fields=("request_id", "agent_name"), name="unique_request_agent_event"),
        ]

    def _prepare_traceability(self) -> None:
        if self.goal_id is None and self.plan_id is not None:
            self.goal_id = self.plan.goal_id
        if self.goal_id is None:
            raise ValueError("AI execution logs must identify their originating academic goal.")

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise TypeError("AI execution logs are immutable.")
        self._prepare_traceability()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise TypeError("AI execution logs are immutable.")

    def __str__(self) -> str:
        return f"{self.agent_name}: {self.status}"
