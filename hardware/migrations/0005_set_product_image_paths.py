from django.db import migrations


def set_image_paths(apps, schema_editor):
    Product = apps.get_model("hardware", "Product")
    slug_to_path = {
        "bormasina-percutie-bosch-gsb-13-re": "hardware/img/products/bormasina.jpeg",
        "surubelnita-electrica-dewalt-dcf601": "hardware/img/products/surubelnita.jpeg",
        "trusa-scule-108-piese-makita": "hardware/img/products/trusa.jpeg",
        "polizor-unghiular-bosch-gws-750": "hardware/img/products/polizor.jpeg",
        "casti-antifonice-makita-padded": "hardware/img/products/casti.jpeg",
    }
    for slug, path in slug_to_path.items():
        Product.objects.filter(slug=slug).update(image_path=path)
    Product.objects.filter(image_path__isnull=True).update(
        image_path="hardware/img/products/generic.jpeg"
    )


def remove_image_paths(apps, schema_editor):
    Product = apps.get_model("hardware", "Product")
    Product.objects.update(image_path=None)


class Migration(migrations.Migration):
    dependencies = [
        ("hardware", "0004_product_image_path"),
    ]

    operations = [
        migrations.RunPython(set_image_paths, remove_image_paths),
    ]
