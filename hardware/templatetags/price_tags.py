from __future__ import annotations

from django import template
from django.conf import settings
from django.template.base import Node, Token
from django.utils.safestring import mark_safe


register = template.Library()


class PriceEurNode(Node):
    def __init__(self, price_var, nodelist):
        self.price_var = template.Variable(price_var)
        self.nodelist = nodelist

    def render(self, context):
        try:
            price = float(self.price_var.resolve(context))
        except Exception:
            return self.nodelist.render(context)
        eur = price / settings.EUR_RATE
        base_text = self.nodelist.render(context).strip()
        if not base_text:
            base_text = f"Pret: {price:.2f} RON"
        html = (
            f'<span class="price-eur">'
            f'{base_text} <span class="eur">({eur:.2f} EUR)</span>'
            f"</span>"
        )
        return mark_safe(html)


@register.tag(name="price_eur")
def price_eur(parser, token: Token):
    bits = token.split_contents()
    if len(bits) != 2:
        raise template.TemplateSyntaxError("price_eur necesita un singur argument (pretul).")
    nodelist = parser.parse(("endprice_eur",))
    parser.delete_first_token()
    return PriceEurNode(bits[1], nodelist)
