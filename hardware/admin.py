from django.contrib import admin

from . import models


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(models.Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "founded_year")
    search_fields = ("name", "country")


@admin.register(models.Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("name", "recyclable")
    list_filter = ("recyclable",)
    search_fields = ("name",)


class AccessoryInline(admin.TabularInline):
    model = models.Accessory
    extra = 1


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "brand", "price", "available")
    list_filter = ("available", "category", "brand")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "category__name", "brand__name")
    inlines = [AccessoryInline]


@admin.register(models.Accessory)
class AccessoryAdmin(admin.ModelAdmin):
    list_display = ("name", "product", "price", "requires_professional_installation")
    list_filter = ("requires_professional_installation", "product__brand")
    search_fields = ("name", "product__name")


@admin.register(models.Tutorial)
class TutorialAdmin(admin.ModelAdmin):
    list_display = ("title", "difficulty", "published_at")
    list_filter = ("difficulty",)
    search_fields = ("title",)
    filter_horizontal = ("products",)
