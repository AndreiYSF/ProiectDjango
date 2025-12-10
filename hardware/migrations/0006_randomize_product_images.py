import random

from django.db import migrations


def set_random_images(apps, schema_editor):
    Product = apps.get_model("hardware", "Product")
    choices = [
        "hardware/img/products/bormasina.jpeg",
        "hardware/img/products/surubelnita.jpeg",
    ]
    for product in Product.objects.all():
        product.image_path = random.choice(choices)
        product.save(update_fields=["image_path"])


def reset_images(apps, schema_editor):
    Product = apps.get_model("hardware", "Product")
    Product.objects.update(image_path=None)


class Migration(migrations.Migration):
    dependencies = [
        ("hardware", "0005_set_product_image_paths"),
    ]

    operations = [
        migrations.RunPython(set_random_images, reset_images),
    ]
