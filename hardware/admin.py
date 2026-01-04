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
                    "image_path",
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


@admin.register(models.ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "viewed_at")
    list_filter = ("viewed_at", "product__category")
    search_fields = ("user__username", "product__name", "product__slug")
    ordering = ("-viewed_at",)


@admin.register(models.Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "expires_at", "discount_percent")
    list_filter = ("expires_at",)
    search_fields = ("name", "subject", "message", "coupon_code")
    filter_horizontal = ("categories",)
    ordering = ("-created_at",)


@admin.register(models.Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "quantity", "purchased_at")
    list_filter = ("purchased_at", "product__category")
    search_fields = ("user__username", "product__name")
    ordering = ("-purchased_at",)


@admin.register(models.Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "rating", "rated_at")
    list_filter = ("rating", "rated_at")
    search_fields = ("user__username", "product__name")
    ordering = ("-rated_at",)


@admin.register(models.FeedbackRequest)
class FeedbackRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "next_send_at", "created_at")
    list_filter = ("next_send_at",)
    search_fields = ("user__username", "product__name")
    ordering = ("next_send_at",)


admin.site.site_header = "Magazin Hardware - Panou de administrare"
admin.site.site_title = "Magazin Hardware Admin"
admin.site.index_title = "Gestionare conținut magazin"
