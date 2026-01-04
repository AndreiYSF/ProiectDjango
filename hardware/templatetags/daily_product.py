from __future__ import annotations

from django import template
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from hardware.models import Product


register = template.Library()


@register.simple_tag
def product_of_day():
    today = timezone.localdate().isoformat()
    cache_key = f"product_of_day:{today}"
    product_id = cache.get(cache_key)
    if product_id is None:
        product = Product.objects.filter(available=True).order_by("?").first()
        if not product:
            return ""
        end_of_day = timezone.localtime().replace(hour=23, minute=59, second=59, microsecond=0)
        ttl = int((end_of_day - timezone.localtime()).total_seconds())
        cache.set(cache_key, product.id, timeout=max(ttl, 60))
    else:
        product = Product.objects.filter(id=product_id, available=True).first()
        if not product:
            cache.delete(cache_key)
            return ""

    url = reverse("hardware:product_detail", kwargs={"slug": product.slug})
    html = (
        f'<div class="daily-product-banner">'
        f'<strong>Produsul zilei:</strong> '
        f'<a href="{url}">{product.name}</a> '
        f'- {product.price} lei'
        f'</div>'
    )
    return mark_safe(html)
