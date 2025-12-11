from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("blog/", include("core.urls")),
    path("cont/", include("accounts.urls")),
    path("", include("hardware.urls")),
]
