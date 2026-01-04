from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("hardware", "0006_randomize_product_images"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Promotion",
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
                ("subject", models.CharField(max_length=120)),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateField()),
                ("discount_percent", models.PositiveIntegerField(default=10)),
                ("coupon_code", models.CharField(blank=True, max_length=30)),
                (
                    "categories",
                    models.ManyToManyField(
                        blank=True,
                        related_name="promotions",
                        to="hardware.category",
                    ),
                ),
            ],
            options={
                "verbose_name": "Promotie",
                "verbose_name_plural": "Promotii",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ProductView",
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
                ("viewed_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="views",
                        to="hardware.product",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="product_views",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Vizualizare produs",
                "verbose_name_plural": "Vizualizari produse",
                "ordering": ["-viewed_at"],
                "indexes": [
                    models.Index(fields=["user", "-viewed_at"], name="productview_user_time_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=["user", "product"], name="unique_user_product_view"),
                ],
            },
        ),
    ]
