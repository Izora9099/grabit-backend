from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0002_processed_webhook"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS payment_id_seq START WITH 1000 INCREMENT BY 1;",
            reverse_sql="DROP SEQUENCE IF EXISTS payment_id_seq;",
        ),
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS payout_id_seq START WITH 1 INCREMENT BY 1;",
            reverse_sql="DROP SEQUENCE IF EXISTS payout_id_seq;",
        ),
    ]
