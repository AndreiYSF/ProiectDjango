from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("hardware", "0003_category_color_hex_category_icon_class"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="image_path",
            field=models.CharField(
                blank=True,
                null=True,
                help_text="Cale relativă în static, ex: hardware/img/products/bormasina.jpg",
                max_length=255,
            ),
        ),
    ]
