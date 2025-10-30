from __future__ import annotations

import json
from datetime import datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import FormView

from .forms import ContactForm, ProductCreateForm, ProductFilterForm
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


class ProductsListView(ListView):
    template_name = "hardware/catalog_list.html"
    context_object_name = "products"
    paginate_by = ProductFilterForm.DEFAULT_PER_PAGE
    form_class = ProductFilterForm

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self.current_category = None
        self.current_brand = None
        self.lock_category = False
        self.filter_form: ProductFilterForm | None = None
        self.per_page = self.form_class.DEFAULT_PER_PAGE
        self.sort_param = ""
        self.query_without_page = ""
        super().setup(request, *args, **kwargs)

    def get_form(self) -> ProductFilterForm:
        if not hasattr(self, "_form"):
            self._form = self.form_class(
                self.request.GET or None,
                category_queryset=Category.objects.order_by("name"),
                brand_queryset=Brand.objects.order_by("name"),
                lock_category=self.lock_category,
                category_instance=self.current_category,
            )
            if self.current_brand is not None:
                self._form.fields["brand"].initial = self.current_brand.pk
        return self._form

    def _query_without_page(self) -> str:
        query = self.request.GET.copy()
        if "page" in query:
            query.pop("page")
        return query.urlencode()

    def get_queryset(self):
        queryset = (
            Product.objects.select_related("category", "brand")
            .prefetch_related("materials")
        )
        if self.current_category:
            queryset = queryset.filter(category=self.current_category)
        if self.current_brand:
            queryset = queryset.filter(brand=self.current_brand)

        form = self.get_form()
        self.filter_form = form

        if form.is_valid():
            data = form.cleaned_data

            if data.get("name"):
                queryset = queryset.filter(name__icontains=data["name"])
            if data.get("slug"):
                queryset = queryset.filter(slug__icontains=data["slug"])
            if data.get("description"):
                queryset = queryset.filter(description__icontains=data["description"])
            if data.get("category"):
                queryset = queryset.filter(category=data["category"])
            if data.get("brand"):
                queryset = queryset.filter(brand=data["brand"])

            availability = data.get("available")
            if availability == "true":
                queryset = queryset.filter(available=True)
            elif availability == "false":
                queryset = queryset.filter(available=False)

            if data.get("condition"):
                queryset = queryset.filter(condition=data["condition"])

            if data.get("price") is not None:
                queryset = queryset.filter(price=data["price"])
            if data.get("price_min") is not None:
                queryset = queryset.filter(price__gte=data["price_min"])
            if data.get("price_max") is not None:
                queryset = queryset.filter(price__lte=data["price_max"])

            if data.get("stock") is not None:
                queryset = queryset.filter(stock=data["stock"])
            if data.get("stock_min") is not None:
                queryset = queryset.filter(stock__gte=data["stock_min"])
            if data.get("stock_max") is not None:
                queryset = queryset.filter(stock__lte=data["stock_max"])

            if data.get("added_after"):
                queryset = queryset.filter(added_at__date__gte=data["added_after"])
            if data.get("added_before"):
                queryset = queryset.filter(added_at__date__lte=data["added_before"])
            if data.get("updated_after"):
                queryset = queryset.filter(updated_at__date__gte=data["updated_after"])
            if data.get("updated_before"):
                queryset = queryset.filter(updated_at__date__lte=data["updated_before"])

            materials = data.get("materials")
            if materials:
                queryset = queryset.filter(materials__in=materials).distinct()

            per_page_value = data.get("per_page") or form.DEFAULT_PER_PAGE
            self.per_page = per_page_value
            if (
                "per_page" in self.request.GET
                and per_page_value != form.DEFAULT_PER_PAGE
            ):
                messages.warning(
                    self.request,
                    "Paginarea a fost modificată; este posibil să fi sărit sau să reapară produse deja vizualizate.",
                )

            if form.altered_category:
                messages.error(
                    self.request,
                    "Categoria a fost resetată deoarece nu poate fi modificată din această pagină.",
                )
        else:
            self.per_page = form.DEFAULT_PER_PAGE

        sort_param = self.request.GET.get("sort")
        order_param = self.request.GET.get("ord")
        if sort_param == "price_asc":
            queryset = queryset.order_by("price", "name")
            self.sort_param = "a"
        elif sort_param == "price_desc":
            queryset = queryset.order_by("-price", "name")
            self.sort_param = "d"
        elif sort_param == "newest":
            queryset = queryset.order_by("-added_at")
            self.sort_param = "newest"
        elif order_param == "a":
            queryset = queryset.order_by("price", "name")
            self.sort_param = "a"
        elif order_param == "d":
            queryset = queryset.order_by("-price", "name")
            self.sort_param = "d"
        else:
            queryset = queryset.order_by("name")
            self.sort_param = ""

        self.query_without_page = self._query_without_page()
        return queryset

    def get_paginate_by(self, queryset):
        return self.per_page or self.form_class.DEFAULT_PER_PAGE

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form or self.get_form()
        context["current_category"] = self.current_category
        context["current_brand"] = self.current_brand
        context["is_category_page"] = self.current_category is not None
        context["order_param"] = self.sort_param
        context["query_without_page"] = self.query_without_page
        context["per_page"] = self.per_page
        context["default_per_page"] = self.form_class.DEFAULT_PER_PAGE
        if self.current_category:
            context["page_title"] = self.current_category.name
            context["category_description"] = self.current_category.description
        elif self.current_brand:
            context["page_title"] = f"Produse {self.current_brand.name}"
            context["category_description"] = ""
        else:
            context["page_title"] = "Toate produsele"
            context["category_description"] = ""
        return context


class CategoryDetailView(ProductsListView):
    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        slug = self.kwargs.get("slug")
        self.current_category = get_object_or_404(
            Category.objects.prefetch_related("products"), slug=slug
        )
        self.lock_category = True


class BrandProductsView(ProductsListView):
    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        slug = self.kwargs.get("slug")
        self.current_brand = get_object_or_404(
            Brand.objects.prefetch_related("products"), slug=slug
        )


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


class ProductCreateView(FormView):
    template_name = "hardware/product_create.html"
    form_class = ProductCreateForm

    def form_valid(self, form: ProductCreateForm):
        product = form.save()
        messages.success(self.request, "Produsul a fost creat cu succes.")
        return redirect("hardware:product_detail", slug=product.slug)


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


class ContactView(FormView):
    template_name = "hardware/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("hardware:contact")

    def form_valid(self, form: ContactForm):
        data = form.normalized_data()
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        full_name = f"{first_name} {last_name}".strip() if first_name else last_name
        message_text = data["message"]

        ContactMessage.objects.create(
            name=full_name,
            email=data["email"],
            message=message_text,
        )

        message_label = dict(ContactForm.MESSAGE_CHOICES).get(
            data["message_type"], "Mesaj"
        )
        subject = f"{message_label} de la {full_name}"
        sender = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
        recipient = getattr(settings, "DEFAULT_FROM_EMAIL", "admin@example.com")
        body_lines = [
            f"Nume: {full_name}",
            f"E-mail: {data['email']}",
            f"Tip mesaj: {message_label}",
            f"Subiect: {data['subject']}",
            f"Minim zile așteptare: {data['min_wait_days']}",
        ]
        if data.get("age_display"):
            body_lines.append(f"Vârstă: {data['age_display']}")
        body_lines.append("")
        body_lines.append(message_text)
        send_mail(subject, "\n".join(body_lines), sender, [recipient])

        messages_dir = Path(__file__).resolve().parent / "mesaje"
        messages_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(timezone.now().timestamp())
        payload = {
            "nume": last_name,
            "prenume": first_name or "",
            "varsta": data.get("age_display"),
            "email": data["email"],
            "tip_mesaj": data["message_type"],
            "subiect": data["subject"],
            "minim_zile_asteptare": data["min_wait_days"],
            "mesaj": message_text,
        }
        file_path = messages_dir / f"mesaj_{timestamp}.json"
        with file_path.open("w", encoding="utf-8") as handler:
            json.dump(payload, handler, ensure_ascii=False, indent=2)

        messages.success(self.request, "Mesajul a fost trimis cu succes.")
        return super().form_valid(form)


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
