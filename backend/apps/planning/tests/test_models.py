from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import Role
from apps.goals.models import AcademicGoal

from ..models import AIExecutionLog, PlanTask, StudyPlan

User = get_user_model()


class PlanningModelTests(TestCase):
    def setUp(self):
        role = Role.objects.get(name=Role.Name.STUDENT)
        self.student = User.objects.create_user(
            email="student@example.com", name="Student", password="ComplexPass123!", role=role
        )
        self.goal = AcademicGoal.objects.create(
            owner=self.student,
            subject="Algorithms",
            description="Learn algorithm design.",
            duration=8,
        )

    def create_plan(self):
        return StudyPlan.objects.create(goal=self.goal, summary="A structured algorithms plan.")

    def test_study_plan_belongs_to_exactly_one_goal(self):
        plan = self.create_plan()
        self.assertEqual(plan.goal, self.goal)
        self.assertEqual(self.goal.study_plan, plan)

    def test_goal_cannot_have_two_study_plans(self):
        self.create_plan()
        with self.assertRaises(IntegrityError), transaction.atomic():
            StudyPlan.objects.create(goal=self.goal, summary="Duplicate plan")

    def test_study_plan_has_generated_status_and_timestamp(self):
        plan = self.create_plan()
        self.assertEqual(plan.status, StudyPlan.Status.GENERATED)
        self.assertIsNotNone(plan.generated_at)

    def test_plan_task_persists_approved_fields_and_relationship(self):
        plan = self.create_plan()
        task = PlanTask.objects.create(
            plan=plan,
            week=1,
            title="Complexity analysis",
            description="Study asymptotic notation.",
            method="Worked examples",
        )
        self.assertEqual(task.plan, plan)
        self.assertEqual(list(plan.tasks.all()), [task])
        self.assertEqual(task.method, "Worked examples")

    def test_duplicate_task_identity_within_week_is_rejected(self):
        plan = self.create_plan()
        values = {
            "plan": plan,
            "week": 1,
            "title": "Complexity analysis",
            "description": "Study asymptotic notation.",
            "method": "Worked examples",
        }
        PlanTask.objects.create(**values)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PlanTask.objects.create(**values)

    def test_execution_log_records_approved_execution_data(self):
        plan = self.create_plan()
        log = AIExecutionLog.objects.create(
            plan=plan,
            agent_name=AIExecutionLog.AgentName.PLANNER,
            status=AIExecutionLog.Status.SUCCEEDED,
            duration_ms=125,
            system_response="Structured output accepted.",
        )
        self.assertEqual(log.plan, plan)
        self.assertEqual(log.agent_name, AIExecutionLog.AgentName.PLANNER)
        self.assertEqual(log.status, AIExecutionLog.Status.SUCCEEDED)
        self.assertIsNotNone(log.timestamp)

    def test_failure_log_can_exist_before_a_plan_is_persisted(self):
        log = AIExecutionLog.objects.create(
            goal=self.goal,
            agent_name=AIExecutionLog.AgentName.PLANNER,
            status=AIExecutionLog.Status.FAILED,
            system_response="Provider boundary failed.",
        )
        self.assertIsNone(log.plan)
        self.assertEqual(log.goal, self.goal)
        self.assertIsNotNone(log.execution_id)

    def test_execution_log_cannot_be_updated_or_deleted_through_domain_operations(self):
        log = AIExecutionLog.objects.create(
            goal=self.goal,
            agent_name=AIExecutionLog.AgentName.EVALUATION,
            status=AIExecutionLog.Status.SUCCEEDED,
        )
        log.status = AIExecutionLog.Status.FAILED
        with self.assertRaises(TypeError):
            log.save()
        with self.assertRaises(TypeError):
            log.delete()
        with self.assertRaises(TypeError):
            AIExecutionLog.objects.filter(pk=log.pk).update(status=AIExecutionLog.Status.FAILED)
        with self.assertRaises(TypeError):
            AIExecutionLog.objects.bulk_update([log], ["status"])
        with self.assertRaises(TypeError):
            AIExecutionLog.objects.filter(pk=log.pk).delete()
        with self.assertRaises(TypeError):
            AIExecutionLog._base_manager.filter(pk=log.pk).update(status=AIExecutionLog.Status.FAILED)
        with self.assertRaises(TypeError):
            AIExecutionLog._base_manager.filter(pk=log.pk).delete()

    def test_pre_plan_log_requires_goal_traceability(self):
        with self.assertRaises(ValueError):
            AIExecutionLog.objects.create(
                agent_name=AIExecutionLog.AgentName.PLANNER,
                status=AIExecutionLog.Status.FAILED,
            )

    def test_bulk_create_requires_goal_traceability(self):
        with self.assertRaises(ValueError):
            AIExecutionLog.objects.bulk_create([
                AIExecutionLog(
                    agent_name=AIExecutionLog.AgentName.PLANNER,
                    status=AIExecutionLog.Status.FAILED,
                )
            ])
