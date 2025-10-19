from __future__ import annotations

from django.db import migrations, models
from django.utils import timezone
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    Category = apps.get_model("hardware", "Category")
    Brand = apps.get_model("hardware", "Brand")
    Tutorial = apps.get_model("hardware", "Tutorial")

    def ensure_unique_slug(model, instance, base_slug: str) -> str:
        slug = base_slug or f"{model.__name__.lower()}-{instance.pk}"
        original = slug
        counter = 1
        while (
            model.objects.filter(slug=slug)
            .exclude(pk=instance.pk)
            .exists()
        ):
            slug = f"{original}-{counter}"
            counter += 1
        return slug

    for category in Category.objects.all():
        base_slug = slugify(category.name)
        category.slug = ensure_unique_slug(Category, category, base_slug)
        category.save(update_fields=["slug"])

    for brand in Brand.objects.all():
        base_slug = slugify(brand.name)
        brand.slug = ensure_unique_slug(Brand, brand, base_slug)
        brand.save(update_fields=["slug"])

    for tutorial in Tutorial.objects.all():
        base_slug = slugify(tutorial.title)
        tutorial.slug = ensure_unique_slug(Tutorial, tutorial, base_slug)
        tutorial.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("hardware", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="brand",
            name="slug",
            field=models.SlugField(blank=True, default="", null=True),
        ),
        migrations.AddField(
            model_name="category",
            name="slug",
            field=models.SlugField(blank=True, default="", null=True),
        ),
        migrations.AddField(
            model_name="tutorial",
            name="slug",
            field=models.SlugField(blank=True, default="", null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="added_at",
            field=models.DateTimeField(
                auto_now_add=True, default=timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="product",
            name="condition",
            field=models.CharField(
                choices=[
                    ("nou", "Nou"),
                    ("resigilat", "Resigilat"),
                    ("second_hand", "Second hand"),
                ],
                default="nou",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="category",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="product",
            name="description",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="product",
            name="stock",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name="category",
            options={
                "ordering": ["name"],
                "verbose_name": "Categorie",
                "verbose_name_plural": "Categorii",
            },
        ),
        migrations.AlterModelOptions(
            name="brand",
            options={
                "ordering": ["name"],
                "verbose_name": "Brand",
                "verbose_name_plural": "Branduri",
            },
        ),
        migrations.AlterModelOptions(
            name="material",
            options={
                "ordering": ["name"],
                "verbose_name": "Material",
                "verbose_name_plural": "Materiale",
            },
        ),
        migrations.AlterModelOptions(
            name="accessory",
            options={
                "ordering": ["name"],
                "verbose_name": "Accesoriu",
                "verbose_name_plural": "Accesorii",
            },
        ),
        migrations.AlterModelOptions(
            name="tutorial",
            options={
                "ordering": ["-published_at"],
                "verbose_name": "Tutorial",
                "verbose_name_plural": "Tutoriale",
            },
        ),
        migrations.RemoveField(
            model_name="product",
            name="created_at",
        ),
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="brand",
            name="slug",
            field=models.SlugField(unique=True),
        ),
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(unique=True),
        ),
        migrations.AlterField(
            model_name="tutorial",
            name="slug",
            field=models.SlugField(unique=True),
        ),
        migrations.AddIndex(
            model_name="brand",
            index=models.Index(fields=["slug"], name="brand_slug_idx"),
        ),
        migrations.AddIndex(
            model_name="category",
            index=models.Index(fields=["slug"], name="category_slug_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["slug"], name="product_slug_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(
                fields=["available", "price"], name="product_avail_price_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="tutorial",
            index=models.Index(fields=["slug"], name="tutorial_slug_idx"),
        ),
        migrations.CreateModel(
            name="RequestLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("path", models.TextField()),
                ("method", models.CharField(max_length=10)),
                ("querystring", models.TextField(blank=True)),
                (
                    "ip",
                    models.GenericIPAddressField(blank=True, null=True),
                ),
                ("user_agent", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Jurnal acces",
                "verbose_name_plural": "Jurnal accesări",
            },
        ),
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("processed", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Mesaj contact",
                "verbose_name_plural": "Mesaje contact",
            },
        ),
        migrations.AddIndex(
            model_name="requestlog",
            index=models.Index(
                fields=["-created_at"], name="requestlog_created_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="requestlog",
            index=models.Index(fields=["path"], name="requestlog_path_idx"),
        ),
    ]
