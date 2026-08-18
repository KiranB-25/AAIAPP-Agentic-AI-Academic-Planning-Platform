import json

from django.test import SimpleTestCase

from apps.goals.models import AcademicGoal

from ..agents import DeterministicPlannerAgent
from ..contracts import ContractValidationError, PlannerMilestone, PlannerOutput
from ..services.exceptions import PlannerInputError
from ..services.validation import validate_planner_output


class DeterministicPlannerAgentTests(SimpleTestCase):
    def setUp(self):
        self.planner = DeterministicPlannerAgent()

    @staticmethod
    def goal(**changes):
        values = {
            "subject": "Data Structures",
            "description": "Master core data structures and their applications.",
            "duration": 8,
            "intensity": "Moderate",
        }
        return AcademicGoal(**(values | changes))

    def test_valid_goal_produces_meaningful_valid_serializable_output(self):
        goal = self.goal()
        output = self.planner.run(goal)

        self.assertIsInstance(output, PlannerOutput)
        self.assertEqual(len(output.milestones), 4)
        self.assertTrue(all(item.title and item.title != goal.subject for item in output.milestones))
        self.assertEqual([item.order for item in output.milestones], [1, 2, 3, 4])
        self.assertEqual(output.milestones[0].start_week, 1)
        self.assertEqual(output.milestones[-1].end_week, goal.duration)
        validate_planner_output(goal, output)
        json.dumps(output.to_dict())

    def test_milestone_ids_and_complete_schedule_are_unique_and_stable(self):
        first = self.planner.run(self.goal())
        second = self.planner.run(self.goal())

        self.assertEqual(first, second)
        self.assertEqual(len({item.milestone_id for item in first.milestones}), len(first.milestones))
        for previous, current in zip(first.milestones, first.milestones[1:]):
            self.assertEqual(current.start_week, previous.end_week + 1)

    def test_short_duration_goals_adapt_without_zero_length_milestones(self):
        for duration in (1, 2, 3):
            output = self.planner.run(self.goal(duration=duration))
            self.assertLessEqual(len(output.milestones), duration)
            self.assertEqual(output.milestones[-1].end_week, duration)
            self.assertTrue(all(item.start_week <= item.end_week for item in output.milestones))

    def test_invalid_duration_is_rejected_including_boolean(self):
        for duration in (0, 17, -1, True, "4"):
            with self.subTest(duration=duration), self.assertRaises(PlannerInputError):
                self.planner.run(self.goal(duration=duration))

    def test_missing_or_malformed_required_input_is_rejected(self):
        for changes in ({"subject": " "}, {"description": ""}):
            with self.subTest(changes=changes), self.assertRaises(PlannerInputError):
                self.planner.run(self.goal(**changes))
        with self.assertRaises(PlannerInputError):
            self.planner.run({"subject": "Data Structures"})

    def test_duplicate_generated_milestones_are_rejected(self):
        with self.assertRaises(ContractValidationError):
            PlannerOutput((
                PlannerMilestone("m1", 1, "Foundations", 1, 1),
                PlannerMilestone("m2", 2, "foundations", 2, 2),
            ))

    def test_planner_does_not_persist_goal_or_plan_data(self):
        goal = self.goal()
        self.planner.run(goal)
        self.assertIsNone(goal.pk)
