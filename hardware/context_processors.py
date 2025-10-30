from .models import Category


def categories_menu(request):
    return {"nav_categories": Category.objects.order_by("name")}
