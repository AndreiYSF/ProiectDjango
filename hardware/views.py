from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView

from .forms import ContactForm
from .models import (
    Brand,
    Category,
    ContactMessage,
    Product,
    RequestLog,
    Tutorial,
)


ROMANIAN_DAYS = [
    "Luni",
    "Marți",
    "Miercuri",
    "Joi",
    "Vineri",
    "Sâmbătă",
    "Duminică",
]

ROMANIAN_MONTHS = [
    "ianuarie",
    "februarie",
    "martie",
    "aprilie",
    "mai",
    "iunie",
    "iulie",
    "august",
    "septembrie",
    "octombrie",
    "noiembrie",
    "decembrie",
]


def afis_data(mode: str | None = None, moment=None) -> str:
    """
    Returnează data și/sau ora într-un format prietenos în limba română.
    mode poate fi None, 'zi' sau 'timp'.
    """
    moment = moment or timezone.localtime()
    zi = f"{ROMANIAN_DAYS[moment.weekday()]}, {moment.day} {ROMANIAN_MONTHS[moment.month - 1]} {moment.year}"
    ora = moment.strftime("%H:%M:%S")

    if mode == "zi":
        return zi
    if mode == "timp":
        return ora
    return f"{zi} {ora}"


class HomeView(TemplateView):
    template_name = "hardware/index.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["sectiuni"] = [
            {
                "titlu": "Produse populare",
                "descriere": (
                    "Descoperă bormașinile, șurubelnițele electrice și accesoriile "
                    "preferate de profesioniști și pasionați de bricolaj."
                ),
            },
            {
                "titlu": "Branduri partenere",
                "descriere": (
                    "Colaborăm cu mărci precum Bosch, DeWalt, Makita sau Black+Decker "
                    "pentru a-ți livra scule de încredere."
                ),
            },
            {
                "titlu": "Promoții curente",
                "descriere": (
                    "Oferta se actualizează săptămânal cu pachete de accesorii și "
                    "discount-uri la colecțiile de sezon."
                ),
            },
        ]
        return context


class AboutView(TemplateView):
    template_name = "hardware/despre.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "misiune": (
                    "Susținem comunitatea de meșteri și constructori prin produse durabile, "
                    "consultanță personalizată și tutoriale structurate pentru toate nivelurile."
                ),
                "valori": [
                    "Calitate verificată pentru fiecare produs introdus în ofertă.",
                    "Consultanță tehnică și suport rapid pentru proiecte DIY și profesionale.",
                    "Respect pentru mediu prin selecția materialelor reciclabile.",
                ],
                "experienta": (
                    "Cu peste 10 ani de activitate, magazinul de hardware a echipat mii de "
                    "ateliere și echipe de construcții din întreaga țară."
                ),
            }
        )
        return context


class CatalogListView(ListView):
    template_name = "hardware/catalog_list.html"
    context_object_name = "products"
    paginate_by = 12

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.filter_errors: List[str] = []
        self.active_filters: Dict[str, Any] = {}
        self.sort_option: str = ""

    def get_queryset(self):
        queryset = (
            Product.objects.select_related("category", "brand")
            .prefetch_related("materials")
            .filter(available=True)
        )
        request = self.request
        self.filter_errors = []
        self.active_filters = {}

        category_slug = self.kwargs.get("category_slug")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
            self.active_filters["category_slug"] = category_slug

        brand_slug = self.kwargs.get("brand_slug")
        if brand_slug:
            queryset = queryset.filter(brand__slug=brand_slug)
            self.active_filters["brand_slug"] = brand_slug

        query_category = request.GET.get("category")
        if query_category:
            queryset = queryset.filter(category__slug=query_category)
            self.active_filters["category"] = query_category

        query_brand = request.GET.get("brand")
        if query_brand:
            queryset = queryset.filter(brand__slug=query_brand)
            self.active_filters["brand"] = query_brand

        min_price = request.GET.get("min_price")
        if min_price:
            try:
                min_decimal = Decimal(min_price)
            except (InvalidOperation, TypeError):
                self.filter_errors.append("Valoarea minimă a prețului nu este validă.")
            else:
                queryset = queryset.filter(price__gte=min_decimal)
                self.active_filters["min_price"] = min_price

        max_price = request.GET.get("max_price")
        if max_price:
            try:
                max_decimal = Decimal(max_price)
            except (InvalidOperation, TypeError):
                self.filter_errors.append("Valoarea maximă a prețului nu este validă.")
            else:
                queryset = queryset.filter(price__lte=max_decimal)
                self.active_filters["max_price"] = max_price

        sort = request.GET.get("sort", "")
        if sort in {"price_asc", "price_desc", "newest"}:
            self.sort_option = sort
            if sort == "price_asc":
                queryset = queryset.order_by("price", "name")
            elif sort == "price_desc":
                queryset = queryset.order_by("-price", "name")
            elif sort == "newest":
                queryset = queryset.order_by("-added_at")
        else:
            self.sort_option = ""
            queryset = queryset.order_by("name")

        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.order_by("name")
        context["brands"] = Brand.objects.order_by("name")
        context["filter_errors"] = self.filter_errors
        context["active_filters"] = self.active_filters
        context["sort_option"] = self.sort_option
        context["sort_options"] = [
            ("", "Implicit"),
            ("price_asc", "Preț crescător"),
            ("price_desc", "Preț descrescător"),
            ("newest", "Cele mai noi"),
        ]
        query = self.request.GET.copy()
        if "page" in query:
            query.pop("page")
        context["current_query"] = query.urlencode()
        return context


class ProductDetailView(DetailView):
    template_name = "hardware/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Product.objects.select_related("category", "brand")
            .prefetch_related("materials", "accessories", "tutorials")
            .filter(available=True)
        )

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["accessories"] = self.object.accessories.all()
        context["related_tutorials"] = self.object.tutorials.all()
        return context


def _get_cart(request: HttpRequest) -> Dict[str, Dict[str, Any]]:
    return request.session.get("cart", {})


def _save_cart(request: HttpRequest, cart: Dict[str, Dict[str, Any]]) -> None:
    request.session["cart"] = cart
    request.session.modified = True


def cart_detail(request: HttpRequest) -> HttpResponse:
    cart = _get_cart(request)
    items = []
    total = Decimal("0")

    for product_id, entry in cart.items():
        price = Decimal(str(entry.get("price", "0")))
        qty = int(entry.get("qty", 0))
        subtotal = price * qty
        total += subtotal
        items.append(
            {
                "product_id": int(product_id),
                "name": entry.get("name"),
                "slug": entry.get("slug"),
                "price": price,
                "qty": qty,
                "subtotal": subtotal,
            }
        )

    context = {
        "items": items,
        "total": total,
    }
    return render(request, "hardware/cart.html", context)


@require_POST
def cart_add(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_object_or_404(Product, slug=slug, available=True)
    cart = _get_cart(request)
    product_key = str(product.pk)
    try:
        qty = int(request.POST.get("qty", 1))
    except (TypeError, ValueError):
        qty = 1
    qty = max(1, min(qty, 999))

    if product_key in cart:
        current_qty = int(cart[product_key].get("qty", 0))
        cart[product_key]["qty"] = max(1, min(current_qty + qty, 999))
    else:
        cart[product_key] = {
            "name": product.name,
            "slug": product.slug,
            "price": str(product.price),
            "qty": qty,
        }

    _save_cart(request, cart)
    return redirect("hardware:cart")


@require_POST
def cart_update(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_object_or_404(Product, slug=slug)
    cart = _get_cart(request)
    product_key = str(product.pk)

    if product_key in cart:
        try:
            qty = int(request.POST.get("qty", 1))
        except (TypeError, ValueError):
            qty = 1
        qty = max(1, min(qty, 999))
        cart[product_key]["qty"] = qty
        _save_cart(request, cart)

    return redirect("hardware:cart")


@require_POST
def cart_remove(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_object_or_404(Product, slug=slug)
    cart = _get_cart(request)
    product_key = str(product.pk)

    if product_key in cart:
        cart.pop(product_key)
        _save_cart(request, cart)

    return redirect("hardware:cart")


class ContactView(TemplateView):
    template_name = "hardware/contact.html"
    form_class = ContactForm

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        form = self.form_class(request.POST)
        if form.is_valid():
            message = ContactMessage.objects.create(
                name=form.cleaned_data["name"],
                email=form.cleaned_data["email"],
                message=form.cleaned_data["message"],
            )
            subject = "Mesaj nou din formularul de contact"
            body = (
                f"De la: {message.name} <{message.email}>\n\n"
                f"Mesaj:\n{message.message}"
            )
            sender = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
            recipient = getattr(settings, "DEFAULT_FROM_EMAIL", "admin@example.com")
            send_mail(subject, body, sender, [recipient])
            return render(
                request,
                "hardware/confirmation.html",
                {"name": message.name},
                status=201,
            )
        return render(request, self.template_name, {"form": form}, status=400)


class TutorialsListView(ListView):
    template_name = "hardware/tutorials_list.html"
    context_object_name = "tutorials"
    paginate_by = 12

    def get_queryset(self):
        return (
            Tutorial.objects.prefetch_related("products")
            .order_by("-published_at")
        )


class TutorialDetailView(DetailView):
    template_name = "hardware/tutorial_detail.html"
    context_object_name = "tutorial"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Tutorial.objects.prefetch_related("products")


class LogListView(ListView):
    template_name = "hardware/log_list.html"
    context_object_name = "logs"
    paginate_by = 25

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.filter_errors: List[str] = []

    def get_queryset(self):
        queryset = RequestLog.objects.all()
        params = self.request.GET
        self.filter_errors = []

        method = params.get("method")
        if method:
            queryset = queryset.filter(method__iexact=method)

        ip = params.get("ip")
        if ip:
            queryset = queryset.filter(ip__icontains=ip)

        path_contains = params.get("path")
        if path_contains:
            queryset = queryset.filter(path__icontains=path_contains)

        tz = timezone.get_current_timezone()
        start = params.get("start")
        if start:
            try:
                start_date = datetime.strptime(start, "%Y-%m-%d").date()
            except ValueError:
                self.filter_errors.append(
                    "Data de început este invalidă. Folosește formatul YYYY-MM-DD."
                )
            else:
                start_dt = timezone.make_aware(datetime.combine(start_date, time.min), tz)
                queryset = queryset.filter(created_at__gte=start_dt)

        end = params.get("end")
        if end:
            try:
                end_date = datetime.strptime(end, "%Y-%m-%d").date()
            except ValueError:
                self.filter_errors.append(
                    "Data de final este invalidă. Folosește formatul YYYY-MM-DD."
                )
            else:
                end_dt = timezone.make_aware(datetime.combine(end_date, time.max), tz)
                queryset = queryset.filter(created_at__lte=end_dt)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["filter_errors"] = self.filter_errors
        context["methods"] = (
            RequestLog.objects.values_list("method", flat=True)
            .distinct()
            .order_by("method")
        )
        params = self.request.GET.copy()
        context["params"] = params
        if "page" in params:
            params.pop("page")
        context["params_encoded"] = params.urlencode()
        return context


def info(request: HttpRequest) -> HttpResponse:
    data_param = request.GET.get("data")
    if data_param not in (None, "zi", "timp", ""):
        data_param = None
        mesaj_param = "Parametrul data poate avea valorile „zi”, „timp” sau să fie omis."
    else:
        mesaj_param = ""

    parametri = []
    for cheie, valori in request.GET.lists():
        for valoare in valori:
            parametri.append((cheie, valoare))

    context = {
        "titlu": "Informații despre server",
        "heading": "Informații despre server",
        "mesaj_param": mesaj_param,
        "moment": afis_data(data_param or None),
        "parametri": parametri,
        "server_info": [
            ("Adresă IP client", request.META.get("REMOTE_ADDR", "necunoscut")),
            ("Metodă HTTP", request.method),
            ("URL accesat", request.get_full_path()),
            ("User-Agent", request.META.get("HTTP_USER_AGENT", "necunoscut")),
            ("Host", request.get_host()),
        ],
    }
    return render(request, "hardware/info.html", context)
