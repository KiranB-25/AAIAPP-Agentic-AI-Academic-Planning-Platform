from rest_framework import serializers

from .models import PlanReview


class PlanReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanReview
        fields = ("id", "study_plan_id", "feedback_text", "decision", "created_at", "updated_at")
        read_only_fields = ("id", "study_plan_id", "created_at", "updated_at")


class ReviewSubmissionSerializer(serializers.Serializer):
    feedback_text = serializers.CharField(trim_whitespace=True)
    decision = serializers.ChoiceField(
        choices=(
            PlanReview.Decision.APPROVED,
            PlanReview.Decision.REVISION_REQUIRED,
        )
    )
