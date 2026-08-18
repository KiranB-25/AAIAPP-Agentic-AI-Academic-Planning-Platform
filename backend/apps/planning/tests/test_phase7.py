import json
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from apps.accounts.models import Role
from apps.goals.models import AcademicGoal

from ..agents import DeterministicContentGeneratorAgent, DeterministicEvaluationAgent, DeterministicPlannerAgent
from ..contracts import AggregatedPlan, AggregatedTask, EvaluationResult, EvaluationStatus
from ..models import AIExecutionLog, PlanTask, StudyPlan
from ..services import AgentOrchestrator, PlanAggregator, StudyPlanGenerationService, StudyPlanPersistenceService
from ..services.exceptions import (
    AggregationError,
    DuplicateStudyPlan,
    FinalPlanValidationError,
    PlanPersistenceError,
    UnauthorizedGoalAccess,
)
from ..services.final_validation import validate_final_plan

User = get_user_model()


class AggregationAndFinalValidationTests(SimpleTestCase):
    def setUp(self):
        self.goal = AcademicGoal(subject="Algorithms", description="Learn algorithm design.", duration=4)
        self.planner = DeterministicPlannerAgent().run(self.goal)
        self.content = DeterministicContentGeneratorAgent().run(self.planner)
        self.evaluation = DeterministicEvaluationAgent().run(self.content)

    def test_valid_outputs_map_to_complete_ordered_serializable_plan(self):
        result = PlanAggregator().aggregate(self.planner, self.content, self.evaluation)
        self.assertEqual([task.task_id for task in result.tasks], [task.task_id for task in self.content.tasks])
        self.assertEqual([task.week for task in result.tasks], [task.week for task in self.content.tasks])
        self.assertTrue(all(task.description and task.method and task.objective for task in result.tasks))
        json.dumps(result.to_dict())

    def test_invalid_evaluation_and_inconsistent_content_are_rejected(self):
        with self.assertRaises(AggregationError):
            PlanAggregator().aggregate(
                self.planner,
                self.content,
                EvaluationResult(EvaluationStatus.INVALID, ("Content is incomplete.",)),
            )
        incomplete = object.__new__(type(self.content))
        object.__setattr__(incomplete, "summary", self.content.summary)
        object.__setattr__(incomplete, "tasks", self.content.tasks[:1])
        with self.assertRaises(AggregationError):
            PlanAggregator().aggregate(self.planner, incomplete, self.evaluation)

    def test_final_validator_rejects_out_of_range_or_unpersistable_tasks(self):
        goal = AcademicGoal(id=1, subject="Algorithms", description="Learn.", duration=2)
        invalid = AggregatedPlan("Summary", (
            AggregatedTask("t1", 3, "Task", "Description", "Practice", "Objective", True),
        ))
        with self.assertRaises(FinalPlanValidationError):
            validate_final_plan(goal, invalid)
        too_long = AggregatedPlan("Summary", (
            AggregatedTask("t1", 1, "x" * 201, "Description", "Practice", "Objective", True),
        ))
        with self.assertRaises(FinalPlanValidationError):
            validate_final_plan(goal, too_long)


class StudyPlanPersistenceTests(TestCase):
    def setUp(self):
        role = Role.objects.get(name=Role.Name.STUDENT)
        self.student = User.objects.create_user(
            email="phase7-student@example.com", name="Student", password="ComplexPass123!", role=role
        )
        self.other_student = User.objects.create_user(
            email="phase7-other@example.com", name="Other", password="ComplexPass123!", role=role
        )
        self.goal = AcademicGoal.objects.create(
            owner=self.student,
            subject="Databases",
            description="Learn relational database design and querying.",
            duration=4,
        )
        planner = DeterministicPlannerAgent().run(self.goal)
        content = DeterministicContentGeneratorAgent().run(planner)
        self.evaluation = DeterministicEvaluationAgent().run(content)
        self.aggregate = PlanAggregator().aggregate(planner, content, self.evaluation)
        self.service = StudyPlanPersistenceService()

    def persist(self, request_id=None):
        return self.service.persist(
            goal=self.goal,
            actor=self.student,
            request_id=request_id or uuid.uuid4(),
            aggregated_plan=self.aggregate,
            evaluation=self.evaluation,
        )

    def test_valid_plan_and_all_tasks_are_persisted_with_lifecycle_and_traceability(self):
        request_id = uuid.uuid4()
        plan = self.persist(request_id)
        self.goal.refresh_from_db()

        self.assertEqual(plan.goal, self.goal)
        self.assertEqual(plan.status, StudyPlan.Status.GENERATED)
        self.assertEqual(self.goal.status, AcademicGoal.Status.PLAN_GENERATED)
        self.assertEqual(plan.tasks.count(), len(self.aggregate.tasks))
        self.assertEqual(list(plan.tasks.values_list("week", flat=True)), [task.week for task in self.aggregate.tasks])
        self.assertEqual(
            list(plan.tasks.values_list("objective", "revision_checkpoint")),
            [(task.objective, task.revision_checkpoint) for task in self.aggregate.tasks],
        )
        self.assertEqual(plan.execution_logs.filter(request_id=request_id).count(), 5)
        self.assertEqual(
            set(plan.execution_logs.values_list("agent_name", flat=True)),
            set(AIExecutionLog.AgentName.values),
        )

    def test_same_request_is_idempotent_without_duplicate_tasks(self):
        request_id = uuid.uuid4()
        first = self.persist(request_id)
        second = self.persist(request_id)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(StudyPlan.objects.count(), 1)
        self.assertEqual(PlanTask.objects.count(), len(self.aggregate.tasks))

    def test_different_request_cannot_overwrite_existing_plan(self):
        self.persist()
        with self.assertRaises(DuplicateStudyPlan):
            self.persist()
        self.assertEqual(StudyPlan.objects.count(), 1)

    def test_unauthorized_actor_cannot_finalize_goal(self):
        with self.assertRaises(UnauthorizedGoalAccess):
            self.service.persist(
                goal=self.goal,
                actor=self.other_student,
                request_id=uuid.uuid4(),
                aggregated_plan=self.aggregate,
                evaluation=self.evaluation,
            )
        self.assertFalse(StudyPlan.objects.exists())

    def test_invalid_evaluation_or_final_plan_creates_nothing(self):
        with self.assertRaises(Exception):
            self.service.persist(
                goal=self.goal,
                actor=self.student,
                request_id=uuid.uuid4(),
                aggregated_plan=self.aggregate,
                evaluation=EvaluationResult(EvaluationStatus.INVALID, ("Rejected.",)),
            )
        self.assertFalse(StudyPlan.objects.exists())

    def test_task_creation_failure_rolls_back_plan_tasks_logs_and_goal_status(self):
        with patch("apps.planning.services.persistence.PlanTask.objects.bulk_create", side_effect=RuntimeError("failure")):
            with self.assertRaises(PlanPersistenceError):
                self.persist()
        self.goal.refresh_from_db()
        self.assertEqual(self.goal.status, AcademicGoal.Status.PENDING)
        self.assertFalse(StudyPlan.objects.exists())
        self.assertFalse(PlanTask.objects.exists())
        self.assertFalse(AIExecutionLog.objects.exists())

    def test_execution_linkage_failure_rolls_back_everything(self):
        with patch("apps.planning.services.persistence.AIExecutionLog.objects.bulk_create", side_effect=RuntimeError("failure")):
            with self.assertRaises(PlanPersistenceError):
                self.persist()
        self.assertFalse(StudyPlan.objects.exists())
        self.assertFalse(PlanTask.objects.exists())

    def test_complete_generation_service_returns_persisted_result(self):
        orchestrator = AgentOrchestrator(
            DeterministicPlannerAgent(),
            DeterministicContentGeneratorAgent(),
            DeterministicEvaluationAgent(),
            PlanAggregator(),
        )
        result = StudyPlanGenerationService(orchestrator, self.service).generate(
            goal=self.goal,
            actor=self.student,
            request_id=uuid.uuid4(),
        )
        self.assertIsInstance(result, StudyPlan)
        self.assertTrue(result.tasks.exists())
