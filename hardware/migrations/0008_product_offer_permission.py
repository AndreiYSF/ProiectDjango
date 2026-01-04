from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("hardware", "0007_promotions_and_views"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="product",
            options={
                "ordering": ["name"],
                "permissions": [("vizualizeaza_oferta", "Poate vizualiza oferta speciala")],
                "verbose_name": "Produs",
                "verbose_name_plural": "Produse",
            },
        ),
    ]
