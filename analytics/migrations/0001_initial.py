from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("shops", "0007_alter_shop_options"),
        ("products", "0007_alter_category_id"),
        ("accounts", "0005_user_is_available"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnalyticsEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(
                    choices=[
                        ("product_viewed", "Product viewed"),
                        ("shop_visited", "Shop visited"),
                        ("wishlist_added", "Wishlist add"),
                        ("order_placed", "Order placed"),
                        ("order_paid", "Order paid"),
                        ("order_completed", "Order completed"),
                    ],
                    db_index=True,
                    max_length=20,
                )),
                ("session_key", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("product", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="analytics_events",
                    to="products.product",
                )),
                ("shop", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="analytics_events",
                    to="shops.shop",
                )),
                ("user", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="analytics_events",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["shop", "event_type", "created_at"],
                        name="analytics_shop_etype_idx",
                    ),
                ],
            },
        ),
    ]
