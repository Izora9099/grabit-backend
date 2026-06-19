from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_agentkycdocument_rejection_note"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_available",
            field=models.BooleanField(
                default=False,
                help_text="Agent online/offline toggle.",
            ),
        ),
    ]
