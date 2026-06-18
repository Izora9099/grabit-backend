from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shops", "0004_alter_kycdocument_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="kycdocument",
            name="rejection_note",
            field=models.TextField(blank=True, default=""),
        ),
    ]
