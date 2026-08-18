def calculate_plan_progress(tasks) -> int:
    """Return the authoritative whole-percent completion for persisted plan tasks."""
    tasks = list(tasks)
    if not tasks:
        return 0
    return round(sum(task.is_completed for task in tasks) * 100 / len(tasks))
