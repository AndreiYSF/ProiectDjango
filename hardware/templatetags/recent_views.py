from __future__ import annotations

from django import template
from django.conf import settings
from django.utils import timezone

from hardware.models import ProductView


register = template.Library()


@register.inclusion_tag("hardware/recent_views.html", takes_context=True)
def recent_views(context):
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return {"recent_products": []}
    today = timezone.localdate()
    views = (
        ProductView.objects.filter(user=request.user, viewed_at__date=today)
        .select_related("product")
        .order_by("-viewed_at")[: settings.VIZ_PROD]
    )
    products = [view.product for view in views]
    return {"recent_products": products}
