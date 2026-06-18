from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_add_delivery_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="agentkycdocument",
            name="rejection_note",
            field=models.TextField(blank=True, default=""),
        ),
    ]
