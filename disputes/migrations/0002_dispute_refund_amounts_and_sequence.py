from django.db import migrations, models


def _create_sequence(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            "CREATE SEQUENCE IF NOT EXISTS dispute_id_seq START WITH 300 INCREMENT BY 1;"
        )


def _drop_sequence(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("DROP SEQUENCE IF EXISTS dispute_id_seq;")


class Migration(migrations.Migration):

    dependencies = [
        ("disputes", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(_create_sequence, reverse_code=_drop_sequence),
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
