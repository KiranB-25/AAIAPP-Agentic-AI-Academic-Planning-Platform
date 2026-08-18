from django.conf import settings
from django.db import models


class ImmutableAuditLogQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise TypeError("Audit logs are immutable.")

    def delete(self):
        raise TypeError("Audit logs are immutable.")


class AuditLog(models.Model):
    class Action(models.TextChoices):
        PLAN_GENERATED = "plan_generated", "Plan generated"
        PLAN_REVIEWED = "plan_reviewed", "Plan reviewed"
        TASK_COMPLETION_CHANGED = "task_completion_changed", "Task completion changed"
        NOTIFICATION_READ = "notification_read", "Notification read"
        PLAN_EXPORTED = "plan_exported", "Plan exported"

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="audit_logs")
    action = models.CharField(max_length=64, choices=Action.choices)
    description = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    objects = ImmutableAuditLogQuerySet.as_manager()

    class Meta:
        ordering = ("-timestamp", "-id")
        base_manager_name = "objects"
        default_manager_name = "objects"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise TypeError("Audit logs are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise TypeError("Audit logs are immutable.")
