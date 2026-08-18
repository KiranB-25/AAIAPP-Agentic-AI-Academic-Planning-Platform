from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Role(models.Model):
    class Name(models.TextChoices):
        STUDENT = "student", "Student"
        SUPERVISOR = "supervisor", "Supervisor"
        ADMINISTRATOR = "administrator", "Administrator"

    name = models.CharField(max_length=32, choices=Name.choices, unique=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return self.get_name_display()


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("status", User.Status.ACTIVE)
        if not extra_fields.get("is_staff") or not extra_fields.get("is_superuser"):
            raise ValueError("Superusers must have is_staff=True and is_superuser=True.")
        role, _ = Role.objects.get_or_create(name=Role.Name.ADMINISTRATOR)
        extra_fields.setdefault("role", role)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        DEACTIVATED = "deactivated", "Deactivated"

    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="users")
    supervisor = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_students"
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    def save(self, *args, **kwargs):
        if self.supervisor_id and self.supervisor.role.name != Role.Name.SUPERVISOR:
            raise ValueError("A student's supervisor must have the supervisor role.")
        if self.supervisor_id and self.role.name != Role.Name.STUDENT:
            raise ValueError("Only students may have a supervisor assignment.")
        self.is_active = self.status == self.Status.ACTIVE
        super().save(*args, **kwargs)

    @property
    def is_account_active(self) -> bool:
        return self.is_active and self.status == self.Status.ACTIVE
