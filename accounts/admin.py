from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


def _is_moderator(user: User) -> bool:
    return user.is_authenticated and user.groups.filter(name="Moderatori").exists()


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
                    "blocat",
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
                    "blocat",
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
        "blocat",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
        "country",
        "email_confirmat",
        "blocat",
    )
    search_fields = ("username", "first_name", "last_name", "email", "phone", "city")
    ordering = ("username",)

    def get_fieldsets(self, request, obj=None):
        if _is_moderator(request.user) and not request.user.is_superuser:
            return (
                (None, {"fields": ("first_name", "last_name", "email", "blocat")}),
            )
        return super().get_fieldsets(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if _is_moderator(request.user) and not request.user.is_superuser:
            return ("username", "password", "is_staff", "is_superuser")
        return super().get_readonly_fields(request, obj)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        user = form.instance
        if user.groups.filter(name="Moderatori").exists() and not user.is_staff:
            user.is_staff = True
            user.save(update_fields=["is_staff"])
