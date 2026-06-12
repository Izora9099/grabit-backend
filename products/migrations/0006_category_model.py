from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


INITIAL_CATEGORIES = [
    ("electronics", "Electronics"),
    ("fashion", "Fashion"),
    ("home", "Home"),
    ("food", "Food"),
    ("sports", "Sports"),
    ("beauty", "Beauty"),
]


def seed_categories(apps, schema_editor):
    Category = apps.get_model("products", "Category")
    now = django.utils.timezone.now()
    for slug, name in INITIAL_CATEGORIES:
        Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "is_active": True, "created_at": now, "updated_at": now},
        )


def migrate_product_categories(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    Category = apps.get_model("products", "Category")
    fallback = Category.objects.first()
    for product in Product.objects.all():
        cat = Category.objects.filter(slug=product.category_old).first() or fallback
        product.category_fk = cat
        product.save(update_fields=["category_fk"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0005_productimage_upload_path"),
    ]

    operations = [
        # 1. Create the Category table
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name_plural": "categories",
                "ordering": ["name"],
            },
        ),

        # 2. Seed the initial six categories
        migrations.RunPython(seed_categories, reverse_code=noop),

        # 3. Rename old CharField so we can reuse the name 'category' for the FK
        migrations.RenameField(
            model_name="product",
            old_name="category",
            new_name="category_old",
        ),

        # 4. Add nullable FK column
        migrations.AddField(
            model_name="product",
            name="category_fk",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="products",
                to="products.category",
            ),
        ),

        # 5. Populate the FK from the old string value
        migrations.RunPython(migrate_product_categories, reverse_code=noop),

        # 6. Make the FK non-nullable now that all rows are populated
        migrations.AlterField(
            model_name="product",
            name="category_fk",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="products",
                to="products.category",
            ),
        ),

        # 7. Drop the old CharField
        migrations.RemoveField(
            model_name="product",
            name="category_old",
        ),

        # 8. Rename category_fk -> category
        migrations.RenameField(
            model_name="product",
            old_name="category_fk",
            new_name="category",
        ),
    ]
