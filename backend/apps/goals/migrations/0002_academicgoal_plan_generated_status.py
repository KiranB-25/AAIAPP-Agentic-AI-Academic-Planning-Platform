from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("goals", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="academicgoal",
            name="status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("plan_generated", "Plan Generated")],
                default="pending",
                max_length=32,
            ),
        ),
    ]
