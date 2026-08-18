from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [migrations.CreateModel(
        name="AuditLog",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("action", models.CharField(choices=[("plan_generated", "Plan generated"), ("plan_reviewed", "Plan reviewed"), ("task_completion_changed", "Task completion changed"), ("notification_read", "Notification read"), ("plan_exported", "Plan exported")], max_length=64)),
            ("description", models.CharField(max_length=255)),
            ("timestamp", models.DateTimeField(auto_now_add=True)),
            ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
            ("user_agent", models.CharField(blank=True, max_length=255)),
            ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="audit_logs", to=settings.AUTH_USER_MODEL)),
        ],
        options={"ordering": ("-timestamp", "-id"), "base_manager_name": "objects", "default_manager_name": "objects"},
    )]
