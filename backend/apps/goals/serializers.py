from rest_framework import serializers

from .models import AcademicGoal


class AcademicGoalSerializer(serializers.ModelSerializer):
    is_editable = serializers.BooleanField(read_only=True)

    class Meta:
        model = AcademicGoal
        fields = (
            "id",
            "subject",
            "description",
            "duration",
            "intensity",
            "status",
            "is_editable",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "status", "is_editable", "created_at", "updated_at")

    def validate(self, attrs):
        ownership_fields = {"owner", "owner_id", "user", "user_id"}
        if ownership_fields.intersection(self.initial_data):
            raise serializers.ValidationError({"owner": "Goal ownership is assigned from the authenticated user."})
        return attrs
