from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField()

    class Meta:
        verbose_name = "Categorie"
        verbose_name_plural = "Categorii"

    def __str__(self) -> str:
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=120)
    country = models.CharField(max_length=80, blank=True)
    founded_year = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Branduri"

    def __str__(self) -> str:
        return self.name


class Material(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    recyclable = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiale"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="products"
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    materials = models.ManyToManyField(
        Material, related_name="products", blank=True
    )

    class Meta:
        verbose_name = "Produs"
        verbose_name_plural = "Produse"
        ordering = ["name"]

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

    def __str__(self) -> str:
        return f"{self.name} ({self.product.name})"


class Tutorial(models.Model):
    title = models.CharField(max_length=200)
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

    def __str__(self) -> str:
        return self.title
