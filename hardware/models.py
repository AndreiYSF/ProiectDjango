from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Categorie"
        verbose_name_plural = "Categorii"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"], name="category_slug_idx"),
        ]

    def __str__(self) -> str:
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    country = models.CharField(max_length=80, blank=True)
    founded_year = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Branduri"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"], name="brand_slug_idx"),
        ]

    def __str__(self) -> str:
        return self.name


class Material(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    recyclable = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiale"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    class Condition(models.TextChoices):
        NEW = "nou", _("Nou")
        REFURBISHED = "resigilat", _("Resigilat")
        USED = "second_hand", _("Second hand")

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="products"
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.NEW,
    )
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    materials = models.ManyToManyField(
        Material, related_name="products", blank=True
    )

    class Meta:
        verbose_name = "Produs"
        verbose_name_plural = "Produse"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"], name="product_slug_idx"),
            models.Index(
                fields=["available", "price"], name="product_avail_price_idx"
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Accessory(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="accessories"
    )
    name = models.CharField(max_length=150)
    compatibility_notes = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    requires_professional_installation = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Accesoriu"
        verbose_name_plural = "Accesorii"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.product.name})"


class Tutorial(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    video_url = models.URLField()
    description = models.TextField()
    duration_minutes = models.IntegerField()
    difficulty = models.CharField(max_length=50)
    published_at = models.DateTimeField()
    products = models.ManyToManyField(
        Product, related_name="tutorials", blank=True
    )

    class Meta:
        verbose_name = "Tutorial"
        verbose_name_plural = "Tutoriale"
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["slug"], name="tutorial_slug_idx"),
        ]

    def __str__(self) -> str:
        return self.title


class RequestLog(models.Model):
    path = models.TextField()
    method = models.CharField(max_length=10)
    querystring = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["-created_at"], name="requestlog_created_idx"
            ),
            models.Index(fields=["path"], name="requestlog_path_idx"),
        ]
        verbose_name = "Jurnal acces"
        verbose_name_plural = "Jurnal accesări"

    def __str__(self) -> str:
        return f"{self.method} {self.path} ({self.created_at:%Y-%m-%d %H:%M})"


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Mesaj contact"
        verbose_name_plural = "Mesaje contact"

    def __str__(self) -> str:
        status = "procesat" if self.processed else "neprocesat"
        return f"{self.name} ({status})"
