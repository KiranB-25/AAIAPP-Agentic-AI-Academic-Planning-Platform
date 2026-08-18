from django.db import IntegrityError

from apps.reviews.models import PlanReview

from .models import Notification


def _create_once(**values):
    try:
        Notification.objects.get_or_create(**values)
    except IntegrityError:
        pass


def notify_plan_ready_for_review(*, plan_id):
    from apps.planning.models import StudyPlan
    plan = StudyPlan.objects.select_related("goal__owner__supervisor").filter(pk=plan_id).first()
    if plan is None or plan.goal.owner.supervisor_id is None:
        return
    _create_once(
        recipient=plan.goal.owner.supervisor,
        study_plan=plan,
        notification_type=Notification.Type.PLAN_READY_FOR_REVIEW,
        defaults={"title": "Study plan ready for review", "message": "An assigned student has a study plan ready for review."},
    )


def notify_review_submitted(*, review_id):
    review = PlanReview.objects.select_related("study_plan__goal__owner").filter(pk=review_id).first()
    if review is None:
        return
    notification_type = {
        PlanReview.Decision.APPROVED: Notification.Type.PLAN_APPROVED,
        PlanReview.Decision.REVISION_REQUIRED: Notification.Type.REVISION_REQUIRED,
    }.get(review.decision, Notification.Type.SUPERVISOR_FEEDBACK)
    title = "Supervisor feedback received"
    if review.decision == PlanReview.Decision.APPROVED:
        title = "Study plan approved"
    elif review.decision == PlanReview.Decision.REVISION_REQUIRED:
        title = "Study plan revision required"
    _create_once(
        recipient=review.study_plan.goal.owner,
        study_plan=review.study_plan,
        notification_type=notification_type,
        defaults={"review": review, "title": title, "message": "Your supervisor has submitted feedback on your study plan."},
    )
