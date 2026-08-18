from typing import Protocol

from apps.goals.models import AcademicGoal

from ..contracts import ContentGenerationOutput, EvaluationResult, PlannerOutput


class PlannerAgent(Protocol):
    def run(self, goal: AcademicGoal) -> PlannerOutput: ...


class ContentGeneratorAgent(Protocol):
    def run(self, planner_output: PlannerOutput) -> ContentGenerationOutput: ...


class EvaluationAgent(Protocol):
    def run(self, content_output: ContentGenerationOutput) -> EvaluationResult: ...
