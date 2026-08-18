import uuid

from django.db import IntegrityError, transaction

from apps.accounts.models import Role
from apps.goals.models import AcademicGoal

from ..contracts import AggregatedPlan, EvaluationResult, EvaluationStatus
from ..models import AIExecutionLog, PlanTask, StudyPlan
from .exceptions import (
    DuplicateStudyPlan,
    GoalNotEligible,
    PlanPersistenceError,
    UnauthorizedGoalAccess,
)
from .final_validation import validate_final_plan


class StudyPlanPersistenceService:
    """Atomically finalize a validated aggregate using explicit ORM field mapping."""

    def persist(
        self,
        *,
        goal: AcademicGoal,
        actor,
        request_id: uuid.UUID,
        aggregated_plan: AggregatedPlan,
        evaluation: EvaluationResult,
    ) -> StudyPlan:
        if not isinstance(request_id, uuid.UUID):
            raise PlanPersistenceError("A valid generation request identity is required.")
        if not self._authorized_owner(goal, actor):
            raise UnauthorizedGoalAccess("The academic goal is not owned by the requesting student.")
        if evaluation.status != EvaluationStatus.VALID:
            raise GoalNotEligible("Only successfully evaluated output can be finalized.")
        validate_final_plan(goal, aggregated_plan)

        completed = StudyPlan.objects.filter(
            execution_logs__request_id=request_id,
            execution_logs__agent_name=AIExecutionLog.AgentName.ORCHESTRATOR,
            execution_logs__status=AIExecutionLog.Status.SUCCEEDED,
        ).first()
        if completed is not None:
            if completed.goal_id != goal.pk:
                raise DuplicateStudyPlan("The generation request is already associated with another goal.")
            return completed

        try:
            with transaction.atomic():
                locked_goal = AcademicGoal.objects.select_for_update().get(pk=goal.pk)
                if not self._authorized_owner(locked_goal, actor):
                    raise UnauthorizedGoalAccess("The academic goal is not owned by the requesting student.")
                if StudyPlan.objects.filter(goal=locked_goal).exists():
                    raise DuplicateStudyPlan("The academic goal already has a finalized study plan.")
                if locked_goal.status != AcademicGoal.Status.PENDING:
                    raise GoalNotEligible("The academic goal is not eligible for plan generation.")

                plan = StudyPlan.objects.create(
                    goal=locked_goal,
                    summary=aggregated_plan.summary,
                    status=StudyPlan.Status.GENERATED,
                )
                PlanTask.objects.bulk_create([
                    PlanTask(
                        plan=plan,
                        week=task.week,
                        title=task.title,
                        description=task.description,
                        method=task.method,
                        objective=task.objective,
                        revision_checkpoint=task.revision_checkpoint,
                    )
                    for task in aggregated_plan.tasks
                ])
                AIExecutionLog.objects.bulk_create([
                    AIExecutionLog(
                        request_id=request_id,
                        goal=locked_goal,
                        plan=plan,
                        agent_name=agent_name,
                        status=AIExecutionLog.Status.SUCCEEDED,
                        system_response="Validated stage completed.",
                    )
                    for agent_name in (
                        AIExecutionLog.AgentName.PLANNER,
                        AIExecutionLog.AgentName.CONTENT_GENERATOR,
                        AIExecutionLog.AgentName.EVALUATION,
                        AIExecutionLog.AgentName.AGGREGATOR,
                        AIExecutionLog.AgentName.ORCHESTRATOR,
                    )
                ])
                locked_goal.status = AcademicGoal.Status.PLAN_GENERATED
                locked_goal.save(update_fields=("status", "updated_at"))
                from apps.audit.models import AuditLog
                from apps.audit.services import record
                record(
                    actor=actor,
                    action=AuditLog.Action.PLAN_GENERATED,
                    description=f"Generated study plan #{plan.pk} for academic goal #{locked_goal.pk}.",
                )
                transaction.on_commit(lambda: _notify_plan_ready(plan.pk))
                return plan
        except (DuplicateStudyPlan, GoalNotEligible, UnauthorizedGoalAccess):
            raise
        except IntegrityError as exc:
            raise DuplicateStudyPlan("The academic goal already has a finalized study plan.") from exc
        except Exception as exc:
            raise PlanPersistenceError("The study plan could not be persisted.") from exc

    @staticmethod
    def _authorized_owner(goal: AcademicGoal, actor) -> bool:
        return bool(
            goal.pk is not None
            and actor is not None
            and actor.pk is not None
            and goal.owner_id == actor.pk
            and actor.is_account_active
            and actor.role.name == Role.Name.STUDENT
        )


def _notify_plan_ready(plan_id: int) -> None:
    from apps.notifications.services import notify_plan_ready_for_review
    notify_plan_ready_for_review(plan_id=plan_id)
