from rest_framework.permissions import BasePermission

from .models import Role


class HasRole(BasePermission):
    allowed_roles: tuple[str, ...] = ()

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_account_active
            and user.role.name in self.allowed_roles
        )


class IsStudent(HasRole):
    allowed_roles = (Role.Name.STUDENT,)


class IsSupervisor(HasRole):
    allowed_roles = (Role.Name.SUPERVISOR,)


class IsAdministrator(HasRole):
    allowed_roles = (Role.Name.ADMINISTRATOR,)
