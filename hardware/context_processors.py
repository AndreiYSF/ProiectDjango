from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .models import Category


def categories_menu(request):
    user = request.user
    can_view_admin_pages = (
        user.is_authenticated and user.groups.filter(name="Administratori_site").exists()
    )
    can_add_product = user.is_authenticated and user.has_perm("hardware.add_product")
    cache_key = "nav_categories"
    categories = cache.get(cache_key)
    if categories is None:
        categories = list(Category.objects.order_by("name"))
        cache.set(cache_key, categories, timeout=60 * 60 * 6)
    return {
        "nav_categories": categories,
        "can_view_admin_pages": can_view_admin_pages,
        "can_add_product": can_add_product,
    }


def support_status(request):
    data_path = settings.BASE_DIR / "hardware" / "data" / "support_schedule.json"
    try:
        schedule = cache.get("support_schedule")
        if schedule is None:
            import json

            with data_path.open("r", encoding="utf-8") as handler:
                schedule = json.load(handler)
            cache.set("support_schedule", schedule, timeout=60 * 60)
    except Exception:
        return {"support_message": "Serviciul \"Relații cu Clienții\" este indisponibil la această oră."}

    now = timezone.localtime()
    weekday = now.strftime("%A").lower()
    day_map = {
        "monday": "luni",
        "tuesday": "marti",
        "wednesday": "miercuri",
        "thursday": "joi",
        "friday": "vineri",
        "saturday": "sambata",
        "sunday": "duminica",
    }
    day_key = day_map.get(weekday, "")
    day_info = schedule.get(day_key, {})
    start = day_info.get("start")
    end = day_info.get("end")
    if start and end:
        start_time = datetime.strptime(start, "%H:%M").time()
        end_time = datetime.strptime(end, "%H:%M").time()
        if start_time <= now.time() <= end_time:
            return {
                "support_message": (
                    f'Puteți contacta azi departamentul "Relații cu clienții" până la ora {end}.'
                )
            }
    return {"support_message": 'Serviciul "Relații cu Clienții" este indisponibil la această oră.'}
