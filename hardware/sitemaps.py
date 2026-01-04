from django.contrib.sitemaps import GenericSitemap, Sitemap
from django.urls import reverse

from core.models import Post
from .models import Brand, Category, Product, Tutorial


class StaticViewSitemap(Sitemap):
    priority = 0.6

    def items(self):
        return [
            "hardware:home",
            "hardware:despre",
            "hardware:products",
            "hardware:catalog",
            "hardware:contact",
            "hardware:tutoriale",
            "core:blog_home",
        ]

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.order_by("name")


class BrandSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Brand.objects.order_by("name")


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Post.objects.order_by("-created_at")

    def lastmod(self, obj):
        return obj.created_at


product_sitemap = GenericSitemap(
    {"queryset": Product.objects.filter(available=True), "date_field": "updated_at"},
    priority=0.8,
)

tutorial_sitemap = GenericSitemap(
    {"queryset": Tutorial.objects.all(), "date_field": "published_at"},
    priority=0.5,
)
