from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("disputes", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS dispute_id_seq START WITH 300 INCREMENT BY 1;",
            reverse_sql="DROP SEQUENCE IF EXISTS dispute_id_seq;",
        ),
        migrations.AddField(
            model_name="dispute",
            name="buyer_refund_amount",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                help_text="Set on partial_refund resolution",
            ),
        ),
        migrations.AddField(
            model_name="dispute",
            name="vendor_release_amount",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                help_text="Set on partial_refund resolution",
            ),
        ),
    ]
