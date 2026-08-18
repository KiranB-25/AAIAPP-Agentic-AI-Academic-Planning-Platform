from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_seed_roles")]
    operations = [migrations.AddField(
        model_name="user", name="supervisor", field=models.ForeignKey(
            blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
            related_name="assigned_students", to="accounts.user"
        )
    )]
