from django.db import migrations


def _create_sequence(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            "CREATE SEQUENCE IF NOT EXISTS order_id_seq START WITH 10001 INCREMENT BY 1;"
        )


def _drop_sequence(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("DROP SEQUENCE IF EXISTS order_id_seq;")


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_alter_order_status"),
    ]

    operations = [
        migrations.RunPython(_create_sequence, reverse_code=_drop_sequence),
    ]
