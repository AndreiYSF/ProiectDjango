from django.contrib import admin
from django.urls import include, path

from accounts import views as accounts_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("confirma_mail/<str:code>/", accounts_views.confirm_email, name="confirm_email"),
    path("blog/", include("core.urls")),
    path("cont/", include("accounts.urls")),
    path("", include("hardware.urls")),
]

handler403 = "hardware.views.custom_403"
