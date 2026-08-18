from apps.goals.models import AcademicGoal

from ..contracts import ContentGenerationOutput, ContractValidationError, PlannerOutput


def validate_planner_output(goal: AcademicGoal, planner_output: PlannerOutput) -> None:
    """Validate milestone scheduling before output reaches a downstream agent."""
    duration = goal.duration
    if type(duration) is not int or duration < 1:
        raise ContractValidationError("Academic goal duration must be a positive integer.")

    previous_end = 0
    for milestone in planner_output.milestones:
        if milestone.end_week > duration:
            raise ContractValidationError("A milestone exceeds the academic goal duration.")
        if milestone.start_week != previous_end + 1:
            raise ContractValidationError("Milestone ranges must be contiguous and non-overlapping.")
        previous_end = milestone.end_week

    if previous_end != duration:
        raise ContractValidationError("Planner milestones must cover the academic goal duration.")


def validate_content_generation(
    planner_output: PlannerOutput,
    content_output: ContentGenerationOutput,
) -> None:
    """Validate Content Generation traceability and milestone-local scheduling."""
    if type(planner_output) is not PlannerOutput:
        raise ContractValidationError("Content Generation requires PlannerOutput.")
    if type(content_output) is not ContentGenerationOutput:
        raise ContractValidationError("Content Generation returned an invalid output type.")

    milestones = {item.milestone_id: item for item in planner_output.milestones}
    covered = set()
    normalized_titles = set()
    expected_order = 1
    previous_week = 0
    checkpoints = set()
    for task in content_output.tasks:
        milestone = milestones.get(task.milestone_id)
        if milestone is None:
            raise ContractValidationError("A generated task references an unknown milestone.")
        if task.order != expected_order:
            raise ContractValidationError("Generated task ordering must be contiguous.")
        if task.week < previous_week:
            raise ContractValidationError("Generated task weeks must follow milestone order.")
        if not milestone.start_week <= task.week <= milestone.end_week:
            raise ContractValidationError("A generated task falls outside its milestone boundaries.")
        normalized_title = task.title.casefold()
        if normalized_title in normalized_titles:
            raise ContractValidationError("Generated tasks must not be duplicated.")
        normalized_titles.add(normalized_title)
        covered.add(task.milestone_id)
        if task.revision_checkpoint:
            checkpoints.add(task.milestone_id)
        expected_order += 1
        previous_week = task.week

    if covered != set(milestones):
        raise ContractValidationError("Every milestone must contain generated content.")
    if checkpoints != set(milestones):
        raise ContractValidationError("Every milestone must include a revision checkpoint.")


def validate_planning_schedule(
    goal: AcademicGoal,
    planner_output: PlannerOutput,
    content_output: ContentGenerationOutput,
) -> None:
    """Validate consistency across the goal, milestones, and generated tasks."""
    validate_planner_output(goal, planner_output)
    validate_content_generation(planner_output, content_output)
    duration = goal.duration

    milestone_by_id = {}
    for milestone in planner_output.milestones:
        if milestone.milestone_id in milestone_by_id:
            raise ContractValidationError("Milestone identities must be unique.")
        milestone_by_id[milestone.milestone_id] = milestone

    seen_task_ids = set()
    milestones_with_tasks = set()
    for task in content_output.tasks:
        if task.task_id in seen_task_ids:
            raise ContractValidationError("Task identities must be unique.")
        seen_task_ids.add(task.task_id)
        milestone = milestone_by_id.get(task.milestone_id)
        if milestone is None:
            raise ContractValidationError("A generated task references an unknown milestone.")
        if task.week > duration:
            raise ContractValidationError("A generated task exceeds the academic goal duration.")
        if not milestone.start_week <= task.week <= milestone.end_week:
            raise ContractValidationError("A generated task falls outside its milestone boundaries.")
        milestones_with_tasks.add(task.milestone_id)

    if milestones_with_tasks != set(milestone_by_id):
        raise ContractValidationError("Every milestone must contain at least one generated task.")
