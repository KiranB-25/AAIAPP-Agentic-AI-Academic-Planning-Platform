from apps.planning.services.progress import calculate_plan_progress
from apps.planning.models import StudyPlan


def student_progress_summary(*, student):
    plans = list(StudyPlan.objects.filter(goal__owner=student).select_related("goal").prefetch_related("tasks"))
    return {
        "student_id": student.id,
        "total_plans": len(plans),
        "plans": [
            {"plan_id": plan.id, "subject": plan.goal.subject, "status": plan.status, "progress": calculate_plan_progress(plan.tasks.all())}
            for plan in plans
        ],
    }


def supervisor_review_summary(*, supervisor):
    plans = list(StudyPlan.objects.filter(goal__owner__supervisor=supervisor).select_related("goal__owner").prefetch_related("tasks"))
    return {
        "assigned_students": len({plan.goal.owner_id for plan in plans}),
        "total_plans": len(plans),
        "pending_reviews": sum(plan.status == "generated" for plan in plans),
        "reviewed_plans": sum(plan.status in {"approved", "revision_required"} for plan in plans),
        "plans": [
            {"plan_id": plan.id, "student_id": plan.goal.owner_id, "subject": plan.goal.subject, "status": plan.status, "progress": calculate_plan_progress(plan.tasks.all())}
            for plan in plans
        ],
    }
