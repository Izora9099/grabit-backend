from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0003_add_id_sequences"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderFinancials",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subtotal", models.PositiveIntegerField(help_text="Sum of items before delivery fee, in XAF")),
                ("delivery_fee", models.PositiveIntegerField(default=0, help_text="Delivery fee charged, in XAF")),
                ("total", models.PositiveIntegerField(help_text="subtotal + delivery_fee, in XAF")),
                ("commission_rate", models.DecimalField(decimal_places=4, help_text="e.g. 0.0500 for 5%", max_digits=6)),
                ("platform_fee", models.PositiveIntegerField(help_text="Platform commission, in XAF")),
                ("seller_amount", models.PositiveIntegerField(help_text="Amount owed to vendor after commission, in XAF")),
                ("buyer_refund_amount", models.PositiveIntegerField(blank=True, help_text="Populated on partial_refund resolution", null=True)),
                ("vendor_release_amount", models.PositiveIntegerField(blank=True, help_text="Populated on partial_refund resolution", null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "order",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="financials",
                        to="orders.order",
                    ),
                ),
            ],
        ),
    ]
