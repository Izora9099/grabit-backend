from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_agentkycdocument"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="delivery_type",
            field=models.CharField(
                choices=[
                    ("intra_city", "Intra-city (same city only)"),
                    ("intercity", "Intercity (across cities)"),
                ],
                default="intra_city",
                help_text="For agents only: whether they deliver within one city or between cities.",
                max_length=12,
            ),
        ),
    ]
