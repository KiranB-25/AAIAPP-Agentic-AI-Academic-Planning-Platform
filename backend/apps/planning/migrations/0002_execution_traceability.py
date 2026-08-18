import uuid

import django.db.models.deletion
from django.db import migrations, models


def populate_execution_traceability(apps, schema_editor):
    AIExecutionLog = apps.get_model("planning", "AIExecutionLog")
    for execution_log in AIExecutionLog.objects.select_related("plan__goal").all().iterator():
        execution_log.execution_id = uuid.uuid4()
        if execution_log.plan_id is not None:
            execution_log.goal_id = execution_log.plan.goal_id
        execution_log.save(update_fields=("execution_id", "goal"))
    if AIExecutionLog.objects.filter(goal__isnull=True, plan__isnull=True).exists():
        raise RuntimeError("Existing AI execution logs without a plan cannot be linked to an academic goal.")


class Migration(migrations.Migration):
    dependencies = [("planning", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="aiexecutionlog",
            name="execution_id",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="aiexecutionlog",
            name="goal",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="ai_execution_logs",
                to="goals.academicgoal",
            ),
        ),
        migrations.RunPython(populate_execution_traceability, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="aiexecutionlog",
            name="execution_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterModelOptions(
            name="aiexecutionlog",
            options={"base_manager_name": "objects", "default_manager_name": "objects", "ordering": ("timestamp", "id")},
        ),
    ]
