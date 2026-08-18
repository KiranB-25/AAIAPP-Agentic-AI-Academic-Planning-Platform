from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("planning", "0004_plan_task_progress")]

    operations = [
        migrations.AddField(
            model_name="plantask",
            name="objective",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="plantask",
            name="revision_checkpoint",
            field=models.BooleanField(default=False),
        ),
    ]
