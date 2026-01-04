from django.apps import AppConfig
from django.db.models.signals import post_migrate


class HardwareConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hardware"
    verbose_name = "Magazin Hardware"

    def ready(self):
        post_migrate.connect(create_default_groups, sender=self)


def create_default_groups(sender, **kwargs):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    from .models import Product

    product_ct = ContentType.objects.get_for_model(Product)
    product_perms = Permission.objects.filter(content_type=product_ct)

    group_products, _ = Group.objects.get_or_create(name="Administratori_produse")
    group_products.permissions.set(product_perms)

    group_site, _ = Group.objects.get_or_create(name="Administratori_site")
    group_site.permissions.set(Permission.objects.all())

    user_model = get_user_model()
    user_ct = ContentType.objects.get_for_model(user_model)
    user_perms = Permission.objects.filter(
        content_type=user_ct,
        codename__in=["view_user", "change_user"],
    )
    group_mod, _ = Group.objects.get_or_create(name="Moderatori")
    group_mod.permissions.set(user_perms)
