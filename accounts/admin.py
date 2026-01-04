from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Contact & address"),
            {
                "fields": (
                    "phone",
                    "country",
                    "county",
                    "city",
                    "street",
                    "birth_date",
                    "newsletter_opt_in",
                    "email_confirmat",
                    "cod",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "phone",
                    "country",
                    "county",
                    "city",
                    "street",
                    "birth_date",
                    "newsletter_opt_in",
                    "email_confirmat",
                    "cod",
                ),
            },
        ),
    )
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "city",
        "country",
        "email_confirmat",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "country", "email_confirmat")
    search_fields = ("username", "first_name", "last_name", "email", "phone", "city")
    ordering = ("username",)
