from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Role, User
from .services import default_student_role, issue_tokens


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = User
        fields = ("id", "name", "email", "role", "status")


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False, validators=[validate_password])

    class Meta:
        model = User
        fields = ("name", "email", "password")

    def create(self, validated_data):
        return User.objects.create_user(role=default_student_role(), **validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class AuthResponseSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(trim_whitespace=False)


class UserManagementSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=Role.Name.choices, write_only=True, required=False)

    class Meta:
        model = User
        fields = ("id", "name", "email", "role", "status")
        read_only_fields = ("id", "name", "email")

    def update(self, instance, validated_data):
        role_name = validated_data.pop("role", None)
        if role_name:
            instance.role = Role.objects.get(name=role_name)
        return super().update(instance, validated_data)
