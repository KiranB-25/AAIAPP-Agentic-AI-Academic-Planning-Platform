from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("planning", "0005_plan_task_learning_information")]

    operations = [
        migrations.AlterField(
            model_name="studyplan",
            name="status",
            field=models.CharField(
                choices=[
                    ("generated", "Generated"),
                    ("approved", "Approved"),
                    ("revision_required", "Revision Required"),
                ],
                default="generated",
                max_length=32,
            ),
        ),
    ]
