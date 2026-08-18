import hashlib

from ..contracts import ContentGenerationOutput, ContractValidationError, GeneratedTask, PlannerOutput
from ..services.exceptions import ContentGenerationInputError
from ..services.validation import validate_content_generation


class DeterministicContentGeneratorAgent:
    """Provider-neutral enrichment of milestones into actionable academic tasks."""

    def run(self, planner_output: PlannerOutput) -> ContentGenerationOutput:
        if type(planner_output) is not PlannerOutput:
            raise ContentGenerationInputError("Content Generation requires valid Planner output.")

        tasks = tuple(
            self._task_for_milestone(milestone, order)
            for order, milestone in enumerate(planner_output.milestones, start=1)
        )
        summary = (
            f"Complete {len(tasks)} ordered academic milestones using active study, "
            "guided practice, and revision checkpoints."
        )
        try:
            output = ContentGenerationOutput(summary, tasks)
            validate_content_generation(planner_output, output)
        except ContractValidationError as exc:
            raise ContentGenerationInputError("Valid content could not be generated from the milestones.") from exc
        return output

    def _task_for_milestone(self, milestone, order: int) -> GeneratedTask:
        action, technique = self._learning_strategy(milestone.title)
        task_title = f"{action}: {milestone.title}"
        description = (
            f"Study the concepts in '{milestone.title}', record concise notes, and complete "
            "a practical check of understanding before the milestone ends."
        )
        objective = (
            f"Explain the key ideas from '{milestone.title}' and demonstrate them through "
            "a completed self-check or practice activity."
        )
        task_id = self._stable_identifier(milestone.milestone_id, order, task_title)
        return GeneratedTask(
            task_id=task_id,
            milestone_id=milestone.milestone_id,
            order=order,
            week=milestone.end_week,
            title=task_title,
            description=description,
            objective=objective,
            techniques=(technique, "Self-assessment"),
            revision_checkpoint=True,
        )

    @staticmethod
    def _learning_strategy(title: str) -> tuple[str, str]:
        normalized = title.casefold()
        if "foundation" in normalized:
            return "Map foundational concepts", "Concept mapping"
        if "apply" in normalized or "practice" in normalized:
            return "Complete guided application", "Deliberate practice"
        if "consolidate" in normalized or "mastery" in normalized or "review" in normalized:
            return "Consolidate and review", "Spaced retrieval"
        return "Develop core understanding", "Active recall"

    @staticmethod
    def _stable_identifier(milestone_id: str, order: int, title: str) -> str:
        value = f"{milestone_id}|{order}|{title.casefold()}".encode("utf-8")
        return f"task-{order}-{hashlib.sha256(value).hexdigest()[:12]}"
