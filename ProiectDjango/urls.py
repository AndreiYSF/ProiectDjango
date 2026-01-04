from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from accounts import views as accounts_views
from hardware import sitemaps as hardware_sitemaps

sitemaps = {
    "static": hardware_sitemaps.StaticViewSitemap,
    "categories": hardware_sitemaps.CategorySitemap,
    "brands": hardware_sitemaps.BrandSitemap,
    "posts": hardware_sitemaps.PostSitemap,
    "products": hardware_sitemaps.product_sitemap,
    "tutorials": hardware_sitemaps.tutorial_sitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("confirma_mail/<str:code>/", accounts_views.confirm_email, name="confirm_email"),
    path("blog/", include("core.urls")),
    path("cont/", include("accounts.urls")),
    path("", include("hardware.urls")),
]

handler403 = "hardware.views.custom_403"
