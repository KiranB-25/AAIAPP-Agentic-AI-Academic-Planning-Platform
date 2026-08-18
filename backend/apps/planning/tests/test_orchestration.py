from django.test import SimpleTestCase

from apps.goals.models import AcademicGoal

from ..contracts import (
    AggregatedPlan,
    ContentGenerationOutput,
    EvaluationResult,
    EvaluationStatus,
    GeneratedTask,
    PlannerMilestone,
    PlannerOutput,
)
from ..services.aggregation import PlanAggregator
from ..services.exceptions import AgentExecutionError, AggregationError, EvaluationRejected, InvalidAgentOutput
from ..services.orchestration import AgentOrchestrator


class EventSink:
    def __init__(self, events):
        self.events = events

    def record(self, stage, status, error=""):
        self.events.append((stage, status))


class PlannerDouble:
    def __init__(self, events, failure=None, output=None):
        self.events, self.failure, self.output = events, failure, output

    def run(self, goal):
        self.events.append("planner")
        if self.failure:
            raise self.failure
        return self.output or PlannerOutput((PlannerMilestone("m1", 1, "Foundations", 1, goal.duration),))


class ContentDouble:
    def __init__(self, events, failure=None, output=None):
        self.events, self.failure, self.output = events, failure, output

    def run(self, planner):
        self.events.append("content")
        if self.failure:
            raise self.failure
        return self.output or ContentGenerationOutput(
            "Structured plan.",
            (GeneratedTask("t1", "m1", 1, 1, "Topic", "Description", "Objective", ("Practice",), True),),
        )


class EvaluationDouble:
    def __init__(self, events, failure=None, result=None):
        self.events, self.failure, self.result = events, failure, result

    def run(self, content):
        self.events.append("evaluation")
        if self.failure:
            raise self.failure
        return self.result or EvaluationResult(EvaluationStatus.VALID)


class AggregatorDouble:
    def __init__(self, events, failure=None):
        self.events, self.failure = events, failure

    def aggregate(self, planner, content, evaluation):
        self.events.append("aggregation")
        if self.failure:
            raise self.failure
        return PlanAggregator().aggregate(planner, content, evaluation)


class AgentOrchestratorTests(SimpleTestCase):
    def setUp(self):
        self.goal = AcademicGoal(subject="Algorithms", description="Learn algorithms", duration=4)
        self.calls = []

    def orchestrator(self, planner=None, content=None, evaluation=None, aggregator=None):
        return AgentOrchestrator(
            planner or PlannerDouble(self.calls),
            content or ContentDouble(self.calls),
            evaluation or EvaluationDouble(self.calls),
            aggregator or AggregatorDouble(self.calls),
        )

    def test_successful_orchestration_uses_approved_order(self):
        result = self.orchestrator().run(self.goal)
        self.assertIsInstance(result, AggregatedPlan)
        self.assertEqual(self.calls, ["planner", "content", "evaluation", "aggregation"])

    def test_execution_sink_receives_structured_stage_results(self):
        stage_events = []
        orchestrator = AgentOrchestrator(
            PlannerDouble(self.calls),
            ContentDouble(self.calls),
            EvaluationDouble(self.calls),
            AggregatorDouble(self.calls),
            EventSink(stage_events),
        )
        orchestrator.run(self.goal)
        self.assertEqual(
            stage_events,
            [("planner", "succeeded"), ("content_generator", "succeeded"), ("evaluation", "succeeded"), ("aggregator", "succeeded")],
        )

    def test_planner_failure_is_wrapped(self):
        with self.assertRaises(AgentExecutionError) as raised:
            self.orchestrator(planner=PlannerDouble(self.calls, RuntimeError("provider unavailable"))).run(self.goal)
        self.assertEqual(raised.exception.stage, "planner")
        self.assertEqual(self.calls, ["planner"])

    def test_content_generation_failure_stops_later_stages(self):
        with self.assertRaises(AgentExecutionError) as raised:
            self.orchestrator(content=ContentDouble(self.calls, RuntimeError("content failed"))).run(self.goal)
        self.assertEqual(raised.exception.stage, "content_generator")
        self.assertEqual(self.calls, ["planner", "content"])

    def test_evaluation_execution_failure_is_wrapped(self):
        with self.assertRaises(AgentExecutionError) as raised:
            self.orchestrator(evaluation=EvaluationDouble(self.calls, RuntimeError("evaluation failed"))).run(self.goal)
        self.assertEqual(raised.exception.stage, "evaluation")
        self.assertEqual(self.calls, ["planner", "content", "evaluation"])

    def test_invalid_evaluation_rejects_before_aggregation(self):
        result = EvaluationResult(EvaluationStatus.INVALID, ("Workload is infeasible.",))
        with self.assertRaises(EvaluationRejected) as raised:
            self.orchestrator(evaluation=EvaluationDouble(self.calls, result=result)).run(self.goal)
        self.assertEqual(raised.exception.issues, ("Workload is infeasible.",))
        self.assertEqual(self.calls, ["planner", "content", "evaluation"])

    def test_content_cannot_reference_unknown_planner_milestone(self):
        invalid_content = ContentGenerationOutput(
            "Structured plan.",
            (GeneratedTask("t1", "unknown", 1, 1, "Topic", "Description", "Objective", ("Practice",)),),
        )
        with self.assertRaises(InvalidAgentOutput):
            self.orchestrator(content=ContentDouble(self.calls, output=invalid_content)).run(self.goal)

    def test_milestone_outside_goal_duration_stops_before_evaluation(self):
        planner = PlannerOutput((PlannerMilestone("m1", 1, "Too long", 1, 5),))
        with self.assertRaises(InvalidAgentOutput):
            self.orchestrator(planner=PlannerDouble(self.calls, output=planner)).run(self.goal)
        self.assertEqual(self.calls, ["planner"])

    def test_overlapping_milestone_ranges_stop_before_evaluation(self):
        planner = PlannerOutput((
            PlannerMilestone("m1", 1, "First", 1, 2),
            PlannerMilestone("m2", 2, "Second", 2, 3),
        ))
        content = ContentGenerationOutput("Structured plan.", (
            GeneratedTask("t1", "m1", 1, 1, "First", "Description", "Objective", ("Practice",)),
            GeneratedTask("t2", "m2", 2, 3, "Second", "Description", "Objective", ("Practice",)),
        ))
        with self.assertRaises(InvalidAgentOutput):
            self.orchestrator(
                planner=PlannerDouble(self.calls, output=planner),
                content=ContentDouble(self.calls, output=content),
            ).run(self.goal)
        self.assertEqual(self.calls, ["planner"])

    def test_task_outside_milestone_boundaries_stops_before_evaluation(self):
        planner = PlannerOutput((
            PlannerMilestone("m1", 1, "Foundations", 1, 1),
            PlannerMilestone("m2", 2, "Application", 2, 4),
        ))
        content = ContentGenerationOutput(
            "Structured plan.",
            (GeneratedTask("t1", "m1", 1, 2, "Late", "Description", "Objective", ("Practice",)),),
        )
        with self.assertRaises(InvalidAgentOutput):
            self.orchestrator(
                planner=PlannerDouble(self.calls, output=planner),
                content=ContentDouble(self.calls, output=content),
            ).run(self.goal)
        self.assertEqual(self.calls, ["planner", "content"])

    def test_task_outside_goal_duration_stops_before_evaluation(self):
        planner = PlannerOutput((PlannerMilestone("m1", 1, "Full duration", 1, 4),))
        content = ContentGenerationOutput(
            "Structured plan.",
            (GeneratedTask("t1", "m1", 1, 5, "Late", "Description", "Objective", ("Practice",)),),
        )
        with self.assertRaises(InvalidAgentOutput):
            self.orchestrator(
                planner=PlannerDouble(self.calls, output=planner),
                content=ContentDouble(self.calls, output=content),
            ).run(self.goal)
        self.assertEqual(self.calls, ["planner", "content"])

    def test_invalid_agent_output_type_is_rejected(self):
        with self.assertRaises(InvalidAgentOutput):
            self.orchestrator(planner=PlannerDouble(self.calls, output="invalid")).run(self.goal)

    def test_aggregation_failure_is_surfaced(self):
        with self.assertRaises(AggregationError):
            self.orchestrator(aggregator=AggregatorDouble(self.calls, RuntimeError("aggregation failed"))).run(self.goal)
        self.assertEqual(self.calls, ["planner", "content", "evaluation", "aggregation"])
