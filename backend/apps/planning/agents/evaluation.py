import json
import re

from ..contracts import ContentGenerationOutput, EvaluationResult, EvaluationStatus, GeneratedTask


class DeterministicEvaluationAgent:
    """Apply a deterministic structural and academic-content quality rubric."""

    def run(self, content_output: ContentGenerationOutput) -> EvaluationResult:
        issues = self._issues(content_output)
        if issues:
            return EvaluationResult(EvaluationStatus.INVALID, tuple(issues))
        return EvaluationResult(EvaluationStatus.VALID)

    def _issues(self, content_output) -> list[str]:
        issues = []
        if type(content_output) is not ContentGenerationOutput:
            return ["Evaluation requires a valid ContentGenerationOutput."]
        if type(content_output.summary) is not str or not content_output.summary.strip():
            issues.append("The generated plan summary is missing.")
        if type(content_output.tasks) is not tuple or not content_output.tasks:
            issues.append("The generated plan must contain tasks.")
            return issues
        if any(type(task) is not GeneratedTask for task in content_output.tasks):
            issues.append("The generated plan contains an invalid task structure.")
            return issues

        identifiers = set()
        titles = set()
        milestone_ids = set()
        previous_week = 0
        for expected_order, task in enumerate(content_output.tasks, start=1):
            prefix = f"Task {expected_order}"
            if task.task_id in identifiers:
                issues.append(f"{prefix} duplicates a task identifier.")
            identifiers.add(task.task_id)
            normalized_title = task.title.strip().casefold() if type(task.title) is str else ""
            if normalized_title in titles:
                issues.append(f"{prefix} duplicates another task title.")
            titles.add(normalized_title)
            if task.order != expected_order:
                issues.append(f"{prefix} has an invalid ordering position.")
            if type(task.week) is not int or task.week < 1 or task.week < previous_week:
                issues.append(f"{prefix} has an invalid schedule position.")
            previous_week = task.week if type(task.week) is int else previous_week
            if not self._text(task.milestone_id):
                issues.append(f"{prefix} has no milestone reference.")
            else:
                milestone_ids.add(task.milestone_id)
            if not self._text(task.title):
                issues.append(f"{prefix} has no actionable title.")
            if not self._text(task.description):
                issues.append(f"{prefix} has no meaningful description.")
            if not self._text(task.objective):
                issues.append(f"{prefix} has no measurable learning objective.")
            if type(task.techniques) is not tuple or not task.techniques or any(not self._text(x) for x in task.techniques):
                issues.append(f"{prefix} has no valid learning technique.")
            if type(task.revision_checkpoint) is not bool or not task.revision_checkpoint:
                issues.append(f"{prefix} has no revision checkpoint.")
            if self._text(task.title) and self._text(task.description) and not self._related(task.title, task.description):
                issues.append(f"{prefix} description is not traceable to its title.")

        try:
            json.dumps(content_output.to_dict())
        except (TypeError, ValueError):
            issues.append("The generated content is not JSON serializable.")
        return issues

    @staticmethod
    def _text(value) -> bool:
        return type(value) is str and bool(value.strip())

    @staticmethod
    def _related(title: str, description: str) -> bool:
        title_terms = {term for term in re.findall(r"[a-z0-9]+", title.casefold()) if len(term) > 3}
        description_terms = set(re.findall(r"[a-z0-9]+", description.casefold()))
        return bool(title_terms & description_terms)
