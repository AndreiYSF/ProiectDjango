from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon_class = models.CharField(max_length=120, blank=True)
    color_hex = models.CharField(max_length=7, blank=True)

    class Meta:
        verbose_name = "Categorie"
        verbose_name_plural = "Categorii"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"], name="category_slug_idx"),
        ]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("hardware:category_detail", kwargs={"slug": self.slug})


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

    def get_absolute_url(self):
        return reverse("hardware:brand_detail", kwargs={"slug": self.slug})


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

    def get_absolute_url(self):
        return reverse("hardware:product_detail", kwargs={"slug": self.slug})


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
    image_path = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Cale relativă în static, ex: hardware/img/products/bormasina.jpg",
    )
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
        permissions = [
            ("vizualizeaza_oferta", "Poate vizualiza oferta speciala"),
        ]
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

    def get_absolute_url(self):
        return reverse("hardware:tutorial_detail", kwargs={"slug": self.slug})


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


class ProductView(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_views",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="views",
    )
    viewed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Vizualizare produs"
        verbose_name_plural = "Vizualizari produse"
        ordering = ["-viewed_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="unique_user_product_view")
        ]
        indexes = [
            models.Index(fields=["user", "-viewed_at"], name="productview_user_time_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.product} ({self.viewed_at:%Y-%m-%d %H:%M})"


class Promotion(models.Model):
    name = models.CharField(max_length=120)
    subject = models.CharField(max_length=120)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateField()
    discount_percent = models.PositiveIntegerField(default=10)
    coupon_code = models.CharField(max_length=30, blank=True)
    categories = models.ManyToManyField(Category, related_name="promotions", blank=True)

    class Meta:
        verbose_name = "Promotie"
        verbose_name_plural = "Promotii"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.expires_at:%Y-%m-%d})"
