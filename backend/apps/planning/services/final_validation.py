import json

from apps.goals.models import AcademicGoal

from ..contracts import AggregatedPlan
from .exceptions import FinalPlanValidationError


def validate_final_plan(goal: AcademicGoal, plan: AggregatedPlan) -> None:
    """Validate the complete DTO before any ORM write is attempted."""
    if type(goal) is not AcademicGoal or goal.pk is None:
        raise FinalPlanValidationError("A persisted AcademicGoal is required.")
    if type(plan) is not AggregatedPlan:
        raise FinalPlanValidationError("The aggregated plan has an invalid structure.")

    task_ids = set()
    previous_week = 0
    for task in plan.tasks:
        if task.task_id in task_ids:
            raise FinalPlanValidationError("The final plan contains duplicate task identifiers.")
        task_ids.add(task.task_id)
        if task.week < previous_week or task.week > goal.duration:
            raise FinalPlanValidationError("The final plan contains an invalid task schedule.")
        if len(task.title) > 200 or len(task.method) > 255:
            raise FinalPlanValidationError("The final plan contains data too long for persistence.")
        if not task.revision_checkpoint:
            raise FinalPlanValidationError("The final plan is missing a required revision checkpoint.")
        previous_week = task.week

    try:
        json.dumps(plan.to_dict())
    except (TypeError, ValueError) as exc:
        raise FinalPlanValidationError("The final plan is not JSON serializable.") from exc
