from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Brand",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("country", models.CharField(blank=True, max_length=80)),
                ("founded_year", models.IntegerField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Brand",
                "verbose_name_plural": "Branduri",
            },
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField()),
            ],
            options={
                "verbose_name": "Categorie",
                "verbose_name_plural": "Categorii",
            },
        ),
        migrations.CreateModel(
            name="Material",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("recyclable", models.BooleanField(default=False)),
            ],
            options={
                "verbose_name": "Material",
                "verbose_name_plural": "Materiale",
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField()),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("stock", models.IntegerField(default=0)),
                ("available", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("brand", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="products", to="hardware.brand")),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="products", to="hardware.category")),
                ("materials", models.ManyToManyField(blank=True, related_name="products", to="hardware.material")),
            ],
            options={
                "verbose_name": "Produs",
                "verbose_name_plural": "Produse",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Tutorial",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("video_url", models.URLField()),
                ("description", models.TextField()),
                ("duration_minutes", models.IntegerField()),
                ("difficulty", models.CharField(max_length=50)),
                ("published_at", models.DateTimeField()),
                ("products", models.ManyToManyField(blank=True, related_name="tutorials", to="hardware.product")),
            ],
            options={
                "verbose_name": "Tutorial",
                "verbose_name_plural": "Tutoriale",
            },
        ),
        migrations.CreateModel(
            name="Accessory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("compatibility_notes", models.TextField(blank=True)),
                ("price", models.DecimalField(decimal_places=2, max_digits=8)),
                ("requires_professional_installation", models.BooleanField(default=False)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="accessories", to="hardware.product")),
            ],
            options={
                "verbose_name": "Accesoriu",
                "verbose_name_plural": "Accesorii",
            },
        ),
    ]
