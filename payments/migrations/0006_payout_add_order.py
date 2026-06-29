import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
        ('payments', '0005_platformconfig'),
    ]

    operations = [
        migrations.AddField(
            model_name='payout',
            name='order',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='agent_payouts',
                to='orders.order',
            ),
        ),
    ]
