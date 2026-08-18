from rest_framework import serializers
from django.utils import timezone

from .models import PlanTask, StudyPlan
from .services.progress import calculate_plan_progress


class PlanTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanTask
        fields = (
            "id", "week", "title", "description", "method", "objective", "revision_checkpoint",
            "is_completed", "completed_at", "updated_at",
        )
        read_only_fields = fields


class PlanTaskCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanTask
        fields = ("is_completed",)

    def update(self, instance, validated_data):
        completed = validated_data["is_completed"]
        if instance.is_completed != completed:
            instance.is_completed = completed
            instance.completed_at = timezone.now() if completed else None
            instance.save(update_fields=("is_completed", "completed_at", "updated_at"))
        return instance


class StudyPlanSerializer(serializers.ModelSerializer):
    tasks = PlanTaskSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = StudyPlan
        fields = ("id", "goal_id", "generated_at", "summary", "status", "progress", "tasks")
        read_only_fields = fields

    def get_progress(self, obj):
        return calculate_plan_progress(obj.tasks.all())


class PlanTaskCompletionResponseSerializer(serializers.Serializer):
    task = PlanTaskSerializer(read_only=True)
    progress = serializers.IntegerField(read_only=True)
