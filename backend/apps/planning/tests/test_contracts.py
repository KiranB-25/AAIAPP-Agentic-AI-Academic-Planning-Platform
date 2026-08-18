import json

from django.test import SimpleTestCase

from ..contracts import (
    ContentGenerationOutput,
    ContractValidationError,
    EvaluationResult,
    EvaluationStatus,
    GeneratedTask,
    PlannerMilestone,
    PlannerOutput,
)
from ..services.aggregation import PlanAggregator
from ..services.exceptions import AggregationError


def planner_output():
    return PlannerOutput((PlannerMilestone("m1", 1, "Foundations", 1, 2),))


def content_output():
    return ContentGenerationOutput(
        summary="A structured plan.",
        tasks=(
            GeneratedTask(
                task_id="t1",
                milestone_id="m1",
                order=1,
                week=1,
                title="Core concepts",
                description="Study foundational concepts.",
                objective="Explain the fundamentals.",
                techniques=("Active recall",),
                revision_checkpoint=True,
            ),
        ),
    )


class AgentContractTests(SimpleTestCase):
    def test_planner_output_is_validated_and_json_serializable(self):
        output = planner_output()
        self.assertEqual(output.milestones[0].start_week, 1)
        self.assertIn('"milestone_id": "m1"', json.dumps(output.to_dict()))

    def test_planner_rejects_empty_duplicate_and_invalid_boundaries(self):
        with self.assertRaises(ContractValidationError):
            PlannerOutput(())
        milestone = PlannerMilestone("m1", 1, "First", 1, 1)
        with self.assertRaises(ContractValidationError):
            PlannerOutput((milestone, PlannerMilestone("m1", 2, "Second", 2, 2)))
        with self.assertRaises(ContractValidationError):
            PlannerOutput((milestone, PlannerMilestone("m2", 2, " first ", 2, 2)))
        with self.assertRaises(ContractValidationError):
            PlannerMilestone("m1", 1, "Invalid", 3, 2)

    def test_content_output_supports_approved_enrichment_fields(self):
        task = content_output().tasks[0]
        self.assertEqual(task.objective, "Explain the fundamentals.")
        self.assertEqual(task.techniques, ("Active recall",))
        self.assertTrue(task.revision_checkpoint)

    def test_content_output_rejects_missing_tasks_and_invalid_task_data(self):
        with self.assertRaises(ContractValidationError):
            ContentGenerationOutput("Summary", ())
        with self.assertRaises(ContractValidationError):
            GeneratedTask("t1", "m1", 1, 0, "Task", "Description", "Objective", ("Technique",))
        with self.assertRaises(ContractValidationError):
            GeneratedTask("t1", "m1", 1, 1, "Task", "Description", "Objective", ())

    def test_contracts_reject_incorrect_collection_and_nested_types(self):
        milestone = PlannerMilestone("m1", 1, "First", 1, 1)
        with self.assertRaises(ContractValidationError):
            PlannerOutput([milestone])
        with self.assertRaises(ContractValidationError):
            PlannerOutput(({"milestone_id": "m1"},))
        with self.assertRaises(ContractValidationError):
            ContentGenerationOutput("Summary", [content_output().tasks[0]])
        with self.assertRaises(ContractValidationError):
            ContentGenerationOutput("Summary", ({"task_id": "t1"},))
        with self.assertRaises(ContractValidationError):
            GeneratedTask("t1", "m1", True, 1, "Task", "Description", "Objective", ("Practice",))
        with self.assertRaises(ContractValidationError):
            GeneratedTask("t1", "m1", 1, 1, "Task", "Description", "Objective", ["Practice"])

    def test_duplicate_task_identifiers_are_rejected(self):
        task = content_output().tasks[0]
        duplicate = GeneratedTask("t1", "m1", 2, 1, "Second", "Description", "Objective", ("Practice",))
        with self.assertRaises(ContractValidationError):
            ContentGenerationOutput("Summary", (task, duplicate))

    def test_evaluation_result_distinguishes_valid_and_invalid(self):
        valid = EvaluationResult(EvaluationStatus.VALID)
        invalid = EvaluationResult(EvaluationStatus.INVALID, ("Sequence is infeasible.",))
        self.assertEqual(valid.status, EvaluationStatus.VALID)
        self.assertEqual(invalid.issues, ("Sequence is infeasible.",))

    def test_evaluation_result_rejects_inconsistent_structures(self):
        with self.assertRaises(ContractValidationError):
            EvaluationResult(EvaluationStatus.VALID, ("Unexpected issue",))
        with self.assertRaises(ContractValidationError):
            EvaluationResult(EvaluationStatus.INVALID)
        with self.assertRaises(ContractValidationError):
            EvaluationResult("unexpected", ("Issue",))
        with self.assertRaises(ContractValidationError):
            EvaluationResult(EvaluationStatus.INVALID, ["Issue"])

    def test_all_accepted_contracts_are_json_serializable(self):
        values = (
            planner_output(),
            content_output(),
            EvaluationResult(EvaluationStatus.VALID),
            PlanAggregator().aggregate(planner_output(), content_output(), EvaluationResult(EvaluationStatus.VALID)),
        )
        for value in values:
            json.dumps(value.to_dict())

    def test_aggregator_accepts_valid_structured_output(self):
        result = PlanAggregator().aggregate(planner_output(), content_output(), EvaluationResult(EvaluationStatus.VALID))
        self.assertEqual(result.summary, "A structured plan.")
        self.assertEqual(result.tasks[0].method, "Active recall")
        json.dumps(result.to_dict())

    def test_aggregator_rejects_invalid_evaluation(self):
        with self.assertRaises(AggregationError):
            PlanAggregator().aggregate(
                planner_output(),
                content_output(),
                EvaluationResult(EvaluationStatus.INVALID, ("Redundant tasks.",)),
            )
