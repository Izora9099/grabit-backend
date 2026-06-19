from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shops", "0005_kycdocument_rejection_note"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shop",
            name="status",
            field=models.CharField(
                choices=[
                    ("active", "Active"),
                    ("suspended", "Suspended"),
                    ("under_review", "Under review"),
                    ("rejected", "Rejected"),
                ],
                default="active",
                max_length=15,
            ),
        ),
    ]
