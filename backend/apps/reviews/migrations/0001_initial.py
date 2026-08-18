from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [("planning", "0005_plan_task_learning_information"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name="PlanReview", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("feedback_text", models.TextField()),
        ("decision", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("revision_required", "Revision Required")], default="pending", max_length=32)),
        ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
        ("study_plan", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="review", to="planning.studyplan")),
        ("supervisor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="plan_reviews", to=settings.AUTH_USER_MODEL)),
    ], options={"ordering": ("-created_at", "-id")})]
