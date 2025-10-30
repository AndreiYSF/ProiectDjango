from django.contrib import admin

from . import models


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon_class", "color_hex")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    fieldsets = (
        (None, {"fields": ("name", "slug")}),
        (
            "Detalii opționale",
            {
                "fields": ("description", "icon_class", "color_hex"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(models.Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "country", "founded_year")
    search_fields = ("name", "slug", "country")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(models.Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("name", "recyclable")
    list_filter = ("recyclable",)
    search_fields = ("name", "description")
    ordering = ("name",)


class AccessoryInline(admin.TabularInline):
    model = models.Accessory
    extra = 1


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "category", "brand", "available", "condition")
    list_filter = ("available", "category", "brand", "condition")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "category__name", "brand__name")
    ordering = ("name",)
    inlines = [AccessoryInline]
    list_per_page = 5
    fieldsets = (
        (
            "Informații principale",
            {
                "fields": (
                    "name",
                    "slug",
                    "category",
                    "brand",
                    "price",
                    "stock",
                    "available",
                    "condition",
                )
            },
        ),
        (
            "Detalii suplimentare",
            {
                "fields": ("description", "materials"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(models.Accessory)
class AccessoryAdmin(admin.ModelAdmin):
    list_display = ("name", "product", "price", "requires_professional_installation")
    list_filter = ("requires_professional_installation", "product__brand")
    search_fields = ("name", "product__name")
    ordering = ("name",)


@admin.register(models.Tutorial)
class TutorialAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "difficulty", "published_at")
    list_filter = ("difficulty",)
    search_fields = ("title", "slug")
    filter_horizontal = ("products",)
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-published_at",)


@admin.register(models.RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ("path", "method", "ip", "created_at")
    list_filter = ("method", "created_at")
    search_fields = ("path", "user_agent", "ip")
    readonly_fields = ("path", "method", "querystring", "ip", "user_agent", "created_at")
    ordering = ("-created_at",)


@admin.register(models.ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "processed", "created_at")
    list_filter = ("processed", "created_at")
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "message", "created_at")
    ordering = ("processed", "-created_at")


admin.site.site_header = "Magazin Hardware - Panou de administrare"
admin.site.site_title = "Magazin Hardware Admin"
admin.site.index_title = "Gestionare conținut magazin"
