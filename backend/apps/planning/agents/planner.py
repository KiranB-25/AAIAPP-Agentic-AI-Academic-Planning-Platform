import hashlib

from apps.goals.models import AcademicGoal

from ..contracts import ContractValidationError, PlannerMilestone, PlannerOutput
from ..services.exceptions import InfeasiblePlanningError, PlannerInputError
from ..services.validation import validate_planner_output


class DeterministicPlannerAgent:
    """Provider-neutral production Planner for milestone-level goal decomposition."""

    _MAX_DURATION_WEEKS = 16

    def run(self, goal: AcademicGoal) -> PlannerOutput:
        subject, description, duration = self._validated_input(goal)
        titles = self._milestone_titles(subject, duration)
        if len(titles) > duration:
            raise InfeasiblePlanningError("The goal duration cannot accommodate the planned milestones.")

        seed = f"{subject.casefold()}|{description.casefold()}|{duration}"
        milestones = []
        start_week = 1
        base_length, extra_weeks = divmod(duration, len(titles))
        for index, title in enumerate(titles, start=1):
            length = base_length + (1 if index <= extra_weeks else 0)
            end_week = start_week + length - 1
            identifier = self._stable_identifier(seed, index, title)
            milestones.append(PlannerMilestone(identifier, index, title, start_week, end_week))
            start_week = end_week + 1

        try:
            output = PlannerOutput(tuple(milestones))
            validate_planner_output(goal, output)
        except ContractValidationError as exc:
            raise InfeasiblePlanningError("The academic goal could not be converted into a valid schedule.") from exc
        return output

    def _validated_input(self, goal: AcademicGoal) -> tuple[str, str, int]:
        if not isinstance(goal, AcademicGoal):
            raise PlannerInputError("Planner input must be an AcademicGoal.")

        subject = self._required_text(goal.subject, "subject")
        description = self._required_text(goal.description, "description")
        duration = goal.duration
        if type(duration) is not int or not 1 <= duration <= self._MAX_DURATION_WEEKS:
            raise PlannerInputError("Academic goal duration must be an integer from 1 to 16 weeks.")
        return subject, description, duration

    @staticmethod
    def _required_text(value: str, field_name: str) -> str:
        if type(value) is not str or not value.strip():
            raise PlannerInputError(f"Academic goal {field_name} is required.")
        return " ".join(value.split())

    @staticmethod
    def _milestone_titles(subject: str, duration: int) -> tuple[str, ...]:
        if duration == 1:
            return (f"Establish and apply foundations in {subject}",)
        if duration == 2:
            return (
                f"Establish foundations in {subject}",
                f"Apply and review {subject}",
            )
        if duration <= 5:
            return (
                f"Establish foundations in {subject}",
                f"Develop core {subject} knowledge",
                f"Apply and consolidate {subject}",
            )
        return (
            f"Establish foundations in {subject}",
            f"Develop core {subject} knowledge",
            f"Apply {subject} through guided practice",
            f"Consolidate and demonstrate {subject} mastery",
        )

    @staticmethod
    def _stable_identifier(seed: str, order: int, title: str) -> str:
        digest = hashlib.sha256(f"{seed}|{order}|{title.casefold()}".encode("utf-8")).hexdigest()[:12]
        return f"milestone-{order}-{digest}"
