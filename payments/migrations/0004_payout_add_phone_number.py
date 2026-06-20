from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0003_add_id_sequences"),
    ]

    operations = [
        migrations.AddField(
            model_name="payout",
            name="phone_number",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
