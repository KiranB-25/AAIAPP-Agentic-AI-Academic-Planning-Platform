from typing import Protocol

from apps.goals.models import AcademicGoal

from ..agents import ContentGeneratorAgent, EvaluationAgent, PlannerAgent
from ..contracts import (
    AggregatedPlan,
    ContentGenerationOutput,
    ContractValidationError,
    EvaluationResult,
    EvaluationStatus,
    PlannerOutput,
)
from .aggregation import PlanAggregatorContract
from .exceptions import AgentExecutionError, AggregationError, EvaluationRejected, InvalidAgentOutput
from .validation import validate_planner_output, validate_planning_schedule


class ExecutionEventSink(Protocol):
    def record(self, stage: str, status: str, error: str = "") -> None: ...


class NullExecutionEventSink:
    def record(self, stage: str, status: str, error: str = "") -> None:
        return None


class AgentOrchestrator:
    """Coordinates injected agents; persistence remains in the application service."""

    def __init__(
        self,
        planner: PlannerAgent,
        content_generator: ContentGeneratorAgent,
        evaluator: EvaluationAgent,
        aggregator: PlanAggregatorContract,
        event_sink: ExecutionEventSink | None = None,
    ):
        self.planner = planner
        self.content_generator = content_generator
        self.evaluator = evaluator
        self.aggregator = aggregator
        self.event_sink = event_sink or NullExecutionEventSink()

    def run(self, goal: AcademicGoal) -> AggregatedPlan:
        result, _evaluation = self.run_for_persistence(goal)
        return result

    def run_for_persistence(self, goal: AcademicGoal) -> tuple[AggregatedPlan, EvaluationResult]:
        planner_output = self._invoke("planner", lambda: self.planner.run(goal), PlannerOutput)
        try:
            validate_planner_output(goal, planner_output)
        except ContractValidationError as exc:
            self.event_sink.record("planner", "failed", str(exc))
            raise InvalidAgentOutput("planner", "The planned milestones are structurally invalid.") from exc
        content_output = self._invoke(
            "content_generator",
            lambda: self.content_generator.run(planner_output),
            ContentGenerationOutput,
        )
        try:
            validate_planning_schedule(goal, planner_output, content_output)
        except ContractValidationError as exc:
            self.event_sink.record("content_generator", "failed", str(exc))
            raise InvalidAgentOutput("content_generator", "The generated schedule is structurally invalid.") from exc
        evaluation = self._invoke(
            "evaluation",
            lambda: self.evaluator.run(content_output),
            EvaluationResult,
        )
        if evaluation.status != EvaluationStatus.VALID:
            self.event_sink.record("evaluation", "failed", "Evaluation rejected the output.")
            raise EvaluationRejected(evaluation.issues)
        try:
            result = self.aggregator.aggregate(planner_output, content_output, evaluation)
            if not isinstance(result, AggregatedPlan):
                raise TypeError("Aggregator returned an invalid output type.")
        except Exception as exc:
            self.event_sink.record("aggregator", "failed", str(exc))
            if isinstance(exc, AggregationError):
                raise
            raise AggregationError("Plan aggregation failed.") from exc
        self.event_sink.record("aggregator", "succeeded")
        return result, evaluation

    def _invoke(self, stage: str, operation, expected_type):
        try:
            result = operation()
        except AgentExecutionError as exc:
            self.event_sink.record(stage, "failed", str(exc))
            raise
        except ContractValidationError as exc:
            self.event_sink.record(stage, "failed", str(exc))
            raise InvalidAgentOutput(stage, f"{stage} returned invalid structured output.") from exc
        except Exception as exc:
            self.event_sink.record(stage, "failed", str(exc))
            raise AgentExecutionError(stage, f"{stage} execution failed.") from exc
        if not isinstance(result, expected_type):
            self.event_sink.record(stage, "failed", "Invalid output type.")
            raise InvalidAgentOutput(stage, f"{stage} returned an invalid output type.")
        self.event_sink.record(stage, "succeeded")
        return result
