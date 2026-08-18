from typing import Protocol

from ..contracts import (
    AggregatedPlan,
    AggregatedTask,
    ContentGenerationOutput,
    EvaluationResult,
    EvaluationStatus,
    PlannerOutput,
)
from .exceptions import AggregationError
from .validation import validate_content_generation


class PlanAggregatorContract(Protocol):
    def aggregate(
        self,
        planner: PlannerOutput,
        content: ContentGenerationOutput,
        evaluation: EvaluationResult,
    ) -> AggregatedPlan: ...


class PlanAggregator:
    """Transforms validated structured output; it does not persist or generate content."""

    def aggregate(
        self,
        planner: PlannerOutput,
        content: ContentGenerationOutput,
        evaluation: EvaluationResult,
    ) -> AggregatedPlan:
        if evaluation.status != EvaluationStatus.VALID:
            raise AggregationError("Only evaluated valid content can be aggregated.")
        try:
            validate_content_generation(planner, content)
        except Exception as exc:
            raise AggregationError("Agent outputs are inconsistent and cannot be aggregated.") from exc
        tasks = tuple(
            AggregatedTask(
                task_id=task.task_id,
                week=task.week,
                title=task.title,
                description=task.description,
                method="; ".join(task.techniques),
                objective=task.objective,
                revision_checkpoint=task.revision_checkpoint,
            )
            for task in content.tasks
        )
        return AggregatedPlan(summary=content.summary, tasks=tasks)
