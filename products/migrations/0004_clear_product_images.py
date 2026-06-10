from django.db import migrations


class Migration(migrations.Migration):
    """
    Deletes all ProductImage rows before the URLField → FileField switch goes
    live. Old rows held Supabase Storage URLs which are meaningless to a
    FileField-backed R2 bucket. Vendors must re-upload after deploy.
    """

    dependencies = [
        ('products', '0003_productimage_image_to_filefield'),
    ]

    operations = [
        migrations.RunSQL(
            sql="DELETE FROM products_productimage;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
