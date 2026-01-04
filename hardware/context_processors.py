from .models import Category


def categories_menu(request):
    user = request.user
    can_view_admin_pages = (
        user.is_authenticated and user.groups.filter(name="Administratori_site").exists()
    )
    can_add_product = user.is_authenticated and user.has_perm("hardware.add_product")
    return {
        "nav_categories": Category.objects.order_by("name"),
        "can_view_admin_pages": can_view_admin_pages,
        "can_add_product": can_add_product,
    }
