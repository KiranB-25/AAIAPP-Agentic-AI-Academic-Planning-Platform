import uuid

from django.db import migrations, models


def populate_request_ids(apps, schema_editor):
    AIExecutionLog = apps.get_model("planning", "AIExecutionLog")
    for log in AIExecutionLog.objects.all().iterator():
        log.request_id = uuid.uuid4()
        log.save(update_fields=("request_id",))


class Migration(migrations.Migration):
    dependencies = [
        ("goals", "0002_academicgoal_plan_generated_status"),
        ("planning", "0002_execution_traceability"),
    ]

    operations = [
        migrations.AddField(
            model_name="aiexecutionlog",
            name="request_id",
            field=models.UUIDField(db_index=True, editable=False, null=True),
        ),
        migrations.RunPython(populate_request_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="aiexecutionlog",
            name="request_id",
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False),
        ),
        migrations.AddConstraint(
            model_name="aiexecutionlog",
            constraint=models.UniqueConstraint(
                fields=("request_id", "agent_name"),
                name="unique_request_agent_event",
            ),
        ),
    ]
