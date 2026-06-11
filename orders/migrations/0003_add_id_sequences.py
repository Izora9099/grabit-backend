from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_alter_order_status"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS order_id_seq START WITH 10001 INCREMENT BY 1;",
            reverse_sql="DROP SEQUENCE IF EXISTS order_id_seq;",
        ),
    ]
