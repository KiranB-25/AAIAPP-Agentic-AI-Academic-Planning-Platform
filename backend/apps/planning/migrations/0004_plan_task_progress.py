from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("planning", "0003_execution_request_identity")]

    operations = [
        migrations.AddField(model_name="plantask", name="is_completed", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="plantask", name="completed_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="plantask", name="updated_at", field=models.DateTimeField(auto_now=True)),
    ]
