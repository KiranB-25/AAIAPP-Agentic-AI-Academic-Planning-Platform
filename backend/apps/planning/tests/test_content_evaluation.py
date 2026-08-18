import json

from django.test import SimpleTestCase

from apps.goals.models import AcademicGoal

from ..agents import (
    DeterministicContentGeneratorAgent,
    DeterministicEvaluationAgent,
    DeterministicPlannerAgent,
)
from ..contracts import (
    ContentGenerationOutput,
    ContractValidationError,
    EvaluationStatus,
    GeneratedTask,
    PlannerMilestone,
    PlannerOutput,
)
from ..services.aggregation import PlanAggregator
from ..services.exceptions import ContentGenerationInputError, EvaluationRejected
from ..services.orchestration import AgentOrchestrator
from ..services.validation import validate_content_generation, validate_planning_schedule


def unsafe_content(summary="Summary", tasks=()):
    output = object.__new__(ContentGenerationOutput)
    object.__setattr__(output, "summary", summary)
    object.__setattr__(output, "tasks", tasks)
    return output


class ContentGeneratorTests(SimpleTestCase):
    def setUp(self):
        self.goal = AcademicGoal(
            subject="Algorithms",
            description="Understand algorithm design and apply common techniques.",
            duration=6,
            intensity="Moderate",
        )
        self.planner_output = DeterministicPlannerAgent().run(self.goal)
        self.generator = DeterministicContentGeneratorAgent()

    def test_valid_planner_output_produces_complete_meaningful_content(self):
        output = self.generator.run(self.planner_output)

        self.assertEqual(
            [task.milestone_id for task in output.tasks],
            [milestone.milestone_id for milestone in self.planner_output.milestones],
        )
        self.assertTrue(all(task.title and task.description and task.objective for task in output.tasks))
        self.assertTrue(all(task.techniques and task.revision_checkpoint for task in output.tasks))
        self.assertEqual([task.order for task in output.tasks], list(range(1, len(output.tasks) + 1)))
        self.assertEqual(
            [task.week for task in output.tasks],
            [milestone.end_week for milestone in self.planner_output.milestones],
        )
        validate_content_generation(self.planner_output, output)
        validate_planning_schedule(self.goal, self.planner_output, output)
        json.dumps(output.to_dict())

    def test_generation_is_deterministic_with_unique_stable_identifiers(self):
        first = self.generator.run(self.planner_output)
        second = self.generator.run(self.planner_output)
        self.assertEqual(first, second)
        self.assertEqual(len({task.task_id for task in first.tasks}), len(first.tasks))

    def test_malformed_planner_input_is_rejected(self):
        for value in (None, {}, "planner"):
            with self.subTest(value=value), self.assertRaises(ContentGenerationInputError):
                self.generator.run(value)

    def test_invalid_references_missing_coverage_and_schedule_are_rejected(self):
        task = self.generator.run(self.planner_output).tasks[0]
        cases = (
            GeneratedTask("bad-ref", "missing", 1, task.week, task.title, task.description, task.objective, task.techniques, True),
            GeneratedTask("bad-week", task.milestone_id, 1, 16, task.title, task.description, task.objective, task.techniques, True),
        )
        for invalid_task in cases:
            with self.subTest(task=invalid_task.task_id), self.assertRaises(ContractValidationError):
                validate_content_generation(self.planner_output, ContentGenerationOutput("Summary", (invalid_task,)))
        with self.assertRaises(ContractValidationError):
            validate_content_generation(
                self.planner_output,
                ContentGenerationOutput("Summary", (task,)),
            )

    def test_duplicate_equivalent_tasks_are_rejected(self):
        first = GeneratedTask("t1", "m1", 1, 1, "Review", "Review concepts", "Explain concepts", ("Recall",), True)
        second = GeneratedTask("t2", "m2", 2, 2, "review", "Different", "Demonstrate", ("Practice",), True)
        planner = PlannerOutput((
            PlannerMilestone("m1", 1, "First", 1, 1),
            PlannerMilestone("m2", 2, "Second", 2, 2),
        ))
        with self.assertRaises(ContractValidationError):
            validate_content_generation(planner, ContentGenerationOutput("Summary", (first, second)))

    def test_content_generation_does_not_persist(self):
        output = self.generator.run(self.planner_output)
        self.assertIsNone(self.goal.pk)
        self.assertTrue(all(not hasattr(task, "pk") for task in output.tasks))


class EvaluationAgentTests(SimpleTestCase):
    def setUp(self):
        goal = AcademicGoal(subject="Databases", description="Learn relational database design.", duration=4)
        planner = DeterministicPlannerAgent().run(goal)
        self.valid_content = DeterministicContentGeneratorAgent().run(planner)
        self.evaluator = DeterministicEvaluationAgent()

    def test_complete_content_returns_serializable_valid_result(self):
        result = self.evaluator.run(self.valid_content)
        self.assertEqual(result.status, EvaluationStatus.VALID)
        self.assertEqual(result.issues, ())
        json.dumps(result.to_dict())

    def test_empty_or_invalid_content_returns_actionable_invalid_result(self):
        values = (None, unsafe_content(tasks=()))
        for value in values:
            with self.subTest(value=value):
                result = self.evaluator.run(value)
                self.assertEqual(result.status, EvaluationStatus.INVALID)
                self.assertTrue(result.issues)

    def test_quality_rubric_rejects_missing_fields_duplicates_and_bad_schedule(self):
        original = self.valid_content.tasks[0]
        bad = object.__new__(GeneratedTask)
        for name, value in vars(original).items():
            object.__setattr__(bad, name, value)
        object.__setattr__(bad, "description", "")
        object.__setattr__(bad, "objective", "")
        object.__setattr__(bad, "techniques", ())
        object.__setattr__(bad, "revision_checkpoint", False)
        object.__setattr__(bad, "week", 0)
        duplicate = object.__new__(GeneratedTask)
        for name, value in vars(original).items():
            object.__setattr__(duplicate, name, value)
        result = self.evaluator.run(unsafe_content(tasks=(bad, duplicate)))
        self.assertEqual(result.status, EvaluationStatus.INVALID)
        self.assertTrue(any("description" in issue for issue in result.issues))
        self.assertTrue(any("objective" in issue for issue in result.issues))
        self.assertTrue(any("technique" in issue for issue in result.issues))
        self.assertTrue(any("revision checkpoint" in issue for issue in result.issues))
        self.assertTrue(any("duplicates" in issue for issue in result.issues))

    def test_issue_order_is_deterministic(self):
        invalid = unsafe_content(summary="", tasks=())
        self.assertEqual(self.evaluator.run(invalid), self.evaluator.run(invalid))

    def test_evaluation_does_not_persist(self):
        self.assertEqual(self.evaluator.run(self.valid_content).status, EvaluationStatus.VALID)


class ProductionPhaseSixOrchestrationTests(SimpleTestCase):
    def setUp(self):
        self.goal = AcademicGoal(subject="Networks", description="Learn computer networking fundamentals.", duration=4)

    def test_production_agents_integrate_in_approved_order(self):
        result = AgentOrchestrator(
            DeterministicPlannerAgent(),
            DeterministicContentGeneratorAgent(),
            DeterministicEvaluationAgent(),
            PlanAggregator(),
        ).run(self.goal)
        self.assertTrue(result.tasks)
        self.assertIsNone(self.goal.pk)

    def test_evaluation_rejection_prevents_aggregation(self):
        class RejectingEvaluator:
            def run(self, content):
                return DeterministicEvaluationAgent().run(unsafe_content(tasks=()))

        class AggregatorMustNotRun:
            def aggregate(self, planner, content, evaluation):
                raise AssertionError("Aggregation must not run after rejection.")

        with self.assertRaises(EvaluationRejected):
            AgentOrchestrator(
                DeterministicPlannerAgent(),
                DeterministicContentGeneratorAgent(),
                RejectingEvaluator(),
                AggregatorMustNotRun(),
            ).run(self.goal)
