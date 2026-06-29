from django.db import migrations


def _create_sequences(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            "CREATE SEQUENCE IF NOT EXISTS payment_id_seq START WITH 1000 INCREMENT BY 1;"
        )
        schema_editor.execute(
            "CREATE SEQUENCE IF NOT EXISTS payout_id_seq START WITH 1 INCREMENT BY 1;"
        )


def _drop_sequences(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("DROP SEQUENCE IF EXISTS payment_id_seq;")
        schema_editor.execute("DROP SEQUENCE IF EXISTS payout_id_seq;")


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0002_processed_webhook"),
    ]

    operations = [
        migrations.RunPython(_create_sequences, reverse_code=_drop_sequences),
    ]
