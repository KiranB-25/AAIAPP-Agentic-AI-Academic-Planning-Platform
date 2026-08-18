from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import Role
from apps.notifications.services import notify_review_submitted

from .models import PlanReview


class ReviewWorkflowService:
    terminal = {PlanReview.Decision.APPROVED, PlanReview.Decision.REVISION_REQUIRED}

    @classmethod
    def submit(cls, *, plan, supervisor, feedback_text, decision):
        if plan.goal.owner.supervisor_id != supervisor.id or supervisor.role.name != Role.Name.SUPERVISOR:
            raise PermissionDenied("You are not assigned to review this study plan.")
        feedback_text = feedback_text.strip()
        if not feedback_text:
            raise ValidationError({"feedback_text": ["Feedback is required."]})
        with transaction.atomic():
            plan = type(plan).objects.select_for_update().get(pk=plan.pk)
            review, created = PlanReview.objects.select_for_update().get_or_create(
                study_plan=plan,
                defaults={"supervisor": supervisor, "feedback_text": feedback_text, "decision": decision},
            )
            if not created:
                if review.supervisor_id != supervisor.id:
                    raise PermissionDenied("This review belongs to another supervisor.")
                if review.decision in cls.terminal:
                    raise ValidationError({"decision": ["A finalized review cannot be changed."]})
                if decision == PlanReview.Decision.PENDING and review.feedback_text == feedback_text:
                    raise ValidationError({"decision": ["This review has already been submitted."]})
                review.feedback_text = feedback_text
                review.decision = decision
                review.save(update_fields=("feedback_text", "decision", "updated_at"))
            plan.status = decision
            plan.save(update_fields=("status",))
            from apps.audit.models import AuditLog
            from apps.audit.services import record
            record(
                actor=supervisor,
                action=AuditLog.Action.PLAN_REVIEWED,
                description=f"Set study plan #{plan.pk} review status to {decision}.",
            )
            transaction.on_commit(lambda: notify_review_submitted(review_id=review.id))
        return review
