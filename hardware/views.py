from __future__ import annotations

import json
import logging
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Count
from django.core.cache import cache
from django.core.mail import send_mail, send_mass_mail
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import FormView

from accounts.utils import send_admin_alert
from .forms import (
    ContactForm,
    ProductCreateForm,
    ProductFilterForm,
    PromotionForm,
)
from .models import (
    Brand,
    Category,
    ContactMessage,
    Product,
    ProductView,
    Promotion,
    Purchase,
    Nota,
    FeedbackRequest,
    RequestLog,
    Tutorial,
)
from .utils import Accesare, get_request_count


logger = logging.getLogger("django")

MAX_RECENT_VIEWS = 5
MIN_VIEWS_FOR_PROMO = 2

PROMO_TEMPLATES = {
    "scule-electrice": "hardware/promotions/promo_scule_electrice.txt",
    "echipamente-protectie": "hardware/promotions/promo_protectie.txt",
}


def _per_page_cache_key(request: HttpRequest) -> str:
    if request.user.is_authenticated:
        return f"per_page:user:{request.user.id}"
    if not request.session.session_key:
        request.session.save()
    return f"per_page:session:{request.session.session_key}"


def render_403(request: HttpRequest, *, titlu: str = "", mesaj_personalizat: str = "") -> HttpResponse:
    count = request.session.get("forbidden_count", 0) + 1
    request.session["forbidden_count"] = count
    context = {
        "titlu": titlu,
        "mesaj_personalizat": mesaj_personalizat,
        "nr_403": count,
        "N_MAX_403": getattr(settings, "N_MAX_403", 5),
    }
    return render(request, "403.html", context, status=403)


def custom_403(request: HttpRequest, exception=None) -> HttpResponse:
    return render_403(
        request,
        titlu="",
        mesaj_personalizat="Accesul la resursa curenta nu este permis.",
    )


def _is_site_admin(user) -> bool:
    return user.is_authenticated and user.groups.filter(name="Administratori_site").exists()


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


def afis_data(mode: str | None = None, moment=None, as_section: bool = True) -> str:
    """
    Returnează HTML pentru secțiunea "Data și ora" sau text simplu.
    mode poate fi None, "zi" sau "timp".
    """
    moment = moment or timezone.localtime()
    zi = (
        f"{ROMANIAN_DAYS[moment.weekday()]}, {moment.day} "
        f"{ROMANIAN_MONTHS[moment.month - 1].capitalize()} {moment.year}."
    )
    ora = moment.strftime("%H:%M:%S")

    if not as_section:
        if mode == "zi":
            return zi
        if mode == "timp":
            return ora
        return f"{zi} {ora}"

    if mode == "zi":
        continut = f"<p>{zi}</p>"
    elif mode == "timp":
        continut = f"<p>{ora}</p>"
    else:
        continut = f"<p>{zi}</p><p>{ora}</p>"

    return f'<section class="data-time"><h2>Data și ora</h2>{continut}</section>'


class HomeView(TemplateView):
    template_name = "hardware/index.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["sectiuni"] = [
            {
                "titlu": "Produse populare",
                "icon": "fa-solid fa-screwdriver-wrench",
                "descriere": (
                    "Descoperă bormașinile, șurubelnițele electrice și accesoriile "
                    "preferate de profesioniști și pasionați de bricolaj."
                ),
            },
            {
                "titlu": "Branduri partenere",
                "icon": "fa-solid fa-industry",
                "descriere": (
                    "Colaborăm cu mărci precum Bosch, DeWalt, Makita sau Black+Decker "
                    "pentru a-ți livra scule de încredere."
                ),
            },
            {
                "titlu": "Promoții curente",
                "icon": "fa-solid fa-tags",
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
    minimalist_slugs = {
        "echipamente-protectie",
        "scule-electrice",
        "scule-manuale",
    }

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        self.current_category = None
        self.current_brand = None
        self.lock_category = False
        self.filter_form: ProductFilterForm | None = None
        self.per_page = self.form_class.DEFAULT_PER_PAGE
        self.sort_param = ""
        self.query_without_page = ""
        self.use_minimalist_filters = True
        self.allowed_advanced_fields = [
            "brand",
            "condition",
            "materials",
        ]
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
            cached_per_page = cache.get(_per_page_cache_key(self.request))
            if cached_per_page:
                self._form.fields["per_page"].initial = cached_per_page
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
        cache_key = _per_page_cache_key(self.request)
        cached_per_page = cache.get(cache_key)

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
            if "per_page" in self.request.GET:
                cache.set(
                    cache_key,
                    per_page_value,
                    timeout=settings.PER_PAGE_CACHE_SECONDS,
                )
            elif cached_per_page:
                per_page_value = cached_per_page
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
            self.per_page = cached_per_page or form.DEFAULT_PER_PAGE

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
        cart = _get_cart(self.request)
        cart_qty = {int(pid): int(entry.get("qty", 0)) for pid, entry in cart.items() if str(pid).isdigit()}
        products = context.get("products", [])
        for product in products:
            product.cart_qty = cart_qty.get(product.id, 0)
        context["cart_qty"] = cart_qty
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
        context["minimalist_category"] = self.use_minimalist_filters
        minimal_list = [
            "name",
            "price_min",
            "price_max",
            "available",
            "per_page",
        ] if self.use_minimalist_filters else []
        context["minimalist_filter_fields"] = minimal_list
        filter_form = context["filter_form"]
        visible_fields = list(filter_form.visible_fields())
        minimal_names = set(minimal_list)
        if self.use_minimalist_filters:
            context["minimal_fields"] = [
                field for field in visible_fields if field.name in minimal_names
            ]
            context["advanced_fields"] = [
                field
                for field in visible_fields
                if field.name not in minimal_names
                and field.name in self.allowed_advanced_fields
            ]
        else:
            context["minimal_fields"] = visible_fields
            context["advanced_fields"] = []
        return context


class CategoryDetailView(ProductsListView):
    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        slug = self.kwargs.get("slug")
        self.current_category = get_object_or_404(
            Category.objects.prefetch_related("products"), slug=slug
        )
        self.lock_category = True
        self.use_minimalist_filters = slug in self.minimalist_slugs


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
        cart = _get_cart(self.request)
        entry = cart.get(str(self.object.pk))
        context["in_cart"] = bool(entry)
        context["cart_qty"] = int(entry.get("qty", 0)) if entry else 0
        if self.request.user.is_authenticated:
            _record_product_view(self.request.user, self.object)
        return context


def _record_product_view(user, product: Product) -> None:
    view, created = ProductView.objects.get_or_create(
        user=user,
        product=product,
        defaults={"viewed_at": timezone.now()},
    )
    if not created:
        view.viewed_at = timezone.now()
        view.save(update_fields=["viewed_at"])
    logger.debug("Vizualizare produs inregistrata: %s / %s", user.username, product.slug)

    views = ProductView.objects.filter(user=user).order_by("-viewed_at")
    if views.count() > MAX_RECENT_VIEWS:
        for stale in views[MAX_RECENT_VIEWS:]:
            stale.delete()
        logger.info("Curatate vizualizari vechi pentru user %s", user.username)


class ProductCreateView(FormView):
    template_name = "hardware/product_create.html"
    form_class = ProductCreateForm

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.has_perm("hardware.add_product"):
            return render_403(
                request,
                titlu="Eroare adaugare produse",
                mesaj_personalizat="Nu ai voie să adaugi produse hardware.",
            )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: ProductCreateForm):
        product = form.save()
        messages.success(self.request, "Produsul a fost creat cu succes.")
        return redirect("hardware:product_detail", slug=product.slug)


def interzis(request: HttpRequest) -> HttpResponse:
    return render_403(
        request,
        titlu="Acces interzis",
        mesaj_personalizat="Nu ai voie să accesezi această pagină.",
    )


def oferta(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated or not request.user.has_perm(
        "hardware.vizualizeaza_oferta"
    ):
        return render_403(
            request,
            titlu="Eroare afisare oferta",
            mesaj_personalizat="Nu ai voie să vizualizezi oferta.",
        )
    return render(request, "hardware/oferta.html")


def accepta_oferta(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return render_403(
            request,
            titlu="Eroare afisare oferta",
            mesaj_personalizat="Nu ai voie să vizualizezi oferta.",
        )
    from django.contrib.auth.models import Permission

    perm = Permission.objects.filter(codename="vizualizeaza_oferta").first()
    if perm:
        request.user.user_permissions.add(perm)
        logger.info("Permisiune oferta acordata pentru %s", request.user.username)
    return redirect("hardware:oferta")


class PromotionView(FormView):
    template_name = "hardware/promotions.html"
    form_class = PromotionForm
    success_url = reverse_lazy("hardware:promotii")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        categories = Category.objects.filter(slug__in=PROMO_TEMPLATES.keys()).order_by("name")
        kwargs["categories_queryset"] = categories
        return kwargs

    def form_valid(self, form: PromotionForm) -> HttpResponse:
        data = form.cleaned_data
        expires_at = timezone.localdate() + timedelta(days=data["duration_days"])
        promotion = Promotion.objects.create(
            name=data["name"],
            subject=data["subject"],
            message=data["message"],
            expires_at=expires_at,
            discount_percent=data["discount_percent"],
            coupon_code=data["coupon_code"],
        )
        categories = data["categories"]
        promotion.categories.set(categories)

        sender = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
        emails = []
        User = get_user_model()
        for category in categories:
            template_name = PROMO_TEMPLATES.get(category.slug)
            if not template_name:
                continue
            user_ids = (
                ProductView.objects.filter(product__category=category)
                .values("user")
                .annotate(cnt=Count("id"))
                .filter(cnt__gte=MIN_VIEWS_FOR_PROMO)
                .values_list("user", flat=True)
            )
            recipients = list(
                User.objects.filter(id__in=user_ids, email_confirmat=True)
                .exclude(email="")
                .values_list("email", flat=True)
            )
            logger.debug("Categorie %s are %s destinatari", category.slug, len(recipients))
            if not recipients:
                logger.warning("Nu exista destinatari pentru categoria %s", category.slug)
                continue
            context = {
                "subject": data["subject"],
                "expires_at": expires_at,
                "message": data["message"],
                "discount_percent": data["discount_percent"],
                "coupon_code": data["coupon_code"],
                "category": category,
            }
            body = render_to_string(template_name, context)
            emails.append((data["subject"], body, sender, recipients))

        if emails:
            send_mass_mail(tuple(emails), fail_silently=False)
            logger.info("Promotii trimise catre %s categorii", len(emails))
        else:
            logger.warning("Nu s-au trimis promotii (fara destinatari).")

        messages.success(self.request, "Promoția a fost salvată și mailurile au fost trimise.")
        return super().form_valid(form)


def _get_cart(request: HttpRequest) -> Dict[str, Dict[str, Any]]:
    return request.session.get("cart", {})


def _save_cart(request: HttpRequest, cart: Dict[str, Dict[str, Any]]) -> None:
    request.session["cart"] = cart
    request.session.modified = True


def _redirect_back(request: HttpRequest) -> HttpResponse:
    fallback = reverse_lazy("hardware:cart")
    return redirect(request.META.get("HTTP_REFERER", fallback))


def cart_detail(request: HttpRequest) -> HttpResponse:
    cart = _get_cart(request)
    items = []
    total = Decimal("0")
    product_ids = [int(pid) for pid in cart.keys() if str(pid).isdigit()]
    products_map = {
        product.id: product
        for product in Product.objects.filter(id__in=product_ids)
    }
    missing_ids = [pid for pid in product_ids if pid not in products_map]
    if missing_ids:
        for pid in missing_ids:
            cart.pop(str(pid), None)
        _save_cart(request, cart)
        messages.warning(request, "Unele produse nu mai sunt disponibile și au fost scoase din coș.")

    cart_updated = False
    for product_id, entry in list(cart.items()):
        product = products_map.get(int(product_id))
        if not product:
            continue
        price = Decimal(str(entry.get("price", "0")))
        qty = int(entry.get("qty", 0))
        if product.stock <= 0:
            cart.pop(str(product_id), None)
            cart_updated = True
            messages.warning(
                request,
                f"{product.name} nu mai este in stoc si a fost scos din cos.",
            )
            continue
        if qty > product.stock:
            qty = product.stock
            cart[str(product_id)]["qty"] = qty
            cart_updated = True
            messages.warning(
                request,
                f"Stoc insuficient pentru {product.name}. Cantitatea a fost ajustata la {qty}.",
            )
        subtotal = price * qty
        total += subtotal
        items.append(
            {
                "product_id": int(product_id),
                "name": product.name,
                "slug": product.slug,
                "price": price,
                "qty": qty,
                "subtotal": subtotal,
                "stock": product.stock,
            }
        )
    if cart_updated:
        _save_cart(request, cart)

    context = {
        "items": items,
        "total": total,
    }
    return render(request, "hardware/cart.html", context)


def cart_local(request: HttpRequest) -> HttpResponse:
    return render(request, "hardware/cart_local.html")


@require_POST
def cart_add(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_object_or_404(Product, slug=slug, available=True)
    cart = _get_cart(request)
    product_key = str(product.pk)
    if product.stock <= 0:
        messages.error(request, "Produsul este momentan epuizat.")
        return _redirect_back(request)
    try:
        qty = int(request.POST.get("qty", 1))
    except (TypeError, ValueError):
        messages.error(request, "Cantitatea introdusa nu este valida. Am folosit 1.")
        qty = 1
    max_qty = min(product.stock, 999)
    if qty > max_qty:
        messages.warning(
            request,
            f"Stoc insuficient. Cantitatea pentru {product.name} a fost limitată la {max_qty}.",
        )
    qty = max(1, min(qty, max_qty))

    if product_key in cart:
        current_qty = int(cart[product_key].get("qty", 0))
        new_qty = current_qty + qty
        if new_qty > max_qty:
            new_qty = max_qty
            messages.warning(
                request,
                f"Stoc insuficient. Cantitatea pentru {product.name} a fost limitată la {max_qty}.",
            )
        cart[product_key]["qty"] = max(1, new_qty)
    else:
        cart[product_key] = {
            "name": product.name,
            "slug": product.slug,
            "price": str(product.price),
            "qty": qty,
        }

    _save_cart(request, cart)
    messages.info(request, f"{product.name} a fost adaugat in cos.")
    return _redirect_back(request)


@require_POST
def cart_update(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_object_or_404(Product, slug=slug)
    cart = _get_cart(request)
    product_key = str(product.pk)

    if product_key in cart:
        raw_qty = request.POST.get("qty", "1")
        raw_qty_value = None
        try:
            qty = int(raw_qty)
            raw_qty_value = qty
        except (TypeError, ValueError):
            messages.error(request, "Cantitatea introdusa nu este valida. Nu am modificat cosul.")
            qty = 1
        max_qty = min(product.stock, 999)
        if max_qty <= 0:
            cart.pop(product_key, None)
            _save_cart(request, cart)
            messages.warning(request, f"{product.name} nu mai este in stoc si a fost scos din cos.")
            return _redirect_back(request)
        qty = max(1, min(qty, max_qty))
        if raw_qty_value is not None and raw_qty_value > max_qty:
            messages.warning(
                request,
                f"Stoc insuficient. Cantitatea pentru {product.name} a fost limitată la {max_qty}.",
            )
        cart[product_key]["qty"] = qty
        _save_cart(request, cart)
        messages.info(request, f"Cosul a fost actualizat pentru {product.name}.")

    return _redirect_back(request)


@require_POST
def cart_remove(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_object_or_404(Product, slug=slug)
    cart = _get_cart(request)
    product_key = str(product.pk)

    if product_key in cart:
        cart.pop(product_key)
        _save_cart(request, cart)
        messages.info(request, f"{product.name} a fost eliminat din cos.")

    return _redirect_back(request)


@require_POST
def cart_increment(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_object_or_404(Product, slug=slug, available=True)
    cart = _get_cart(request)
    product_key = str(product.pk)
    if product.stock <= 0:
        messages.error(request, "Produsul este momentan epuizat.")
        return _redirect_back(request)

    current_qty = int(cart.get(product_key, {}).get("qty", 0))
    max_qty = min(product.stock, 999)
    if current_qty + 1 > max_qty:
        messages.warning(
            request,
            f"Stoc insuficient. Cantitatea pentru {product.name} este deja maximă.",
        )
        return _redirect_back(request)
    cart[product_key] = {
        "name": product.name,
        "slug": product.slug,
        "price": str(product.price),
        "qty": current_qty + 1,
    }
    _save_cart(request, cart)
    messages.info(request, f"Am adaugat un produs {product.name} in cos.")
    return _redirect_back(request)


@require_POST
def cart_decrement(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_object_or_404(Product, slug=slug)
    cart = _get_cart(request)
    product_key = str(product.pk)

    if product_key in cart:
        current_qty = int(cart[product_key].get("qty", 0))
        if current_qty <= 1:
            cart.pop(product_key, None)
            messages.info(request, f"{product.name} a fost eliminat din cos.")
        else:
            cart[product_key]["qty"] = current_qty - 1
            messages.info(request, f"Am scazut cantitatea pentru {product.name}.")
        _save_cart(request, cart)

    return _redirect_back(request)


@login_required
@require_POST
def cart_checkout(request: HttpRequest) -> HttpResponse:
    cart = _get_cart(request)
    if not cart:
        messages.warning(request, "Coșul este gol.")
        return _redirect_back(request)

    product_ids = [int(pid) for pid in cart.keys() if str(pid).isdigit()]
    products = Product.objects.filter(id__in=product_ids)
    products_map = {product.id: product for product in products}
    purchased_any = False

    for product_id, entry in list(cart.items()):
        product = products_map.get(int(product_id))
        if not product:
            cart.pop(product_id, None)
            continue
        qty = int(entry.get("qty", 0))
        if qty <= 0:
            cart.pop(product_id, None)
            continue
        if product.stock <= 0:
            messages.warning(request, f"{product.name} nu mai este in stoc.")
            continue
        buy_qty = min(qty, product.stock)
        Purchase.objects.create(
            user=request.user,
            product=product,
            quantity=buy_qty,
        )
        product.stock -= buy_qty
        if product.stock <= 0:
            product.stock = 0
            product.available = False
        product.save(update_fields=["stock", "available"])
        purchased_any = True
        cart.pop(product_id, None)
        if buy_qty < qty:
            messages.warning(
                request,
                f"Stoc insuficient pentru {product.name}. Au fost cumparate doar {buy_qty} buc.",
            )

    _save_cart(request, cart)
    if purchased_any:
        messages.success(request, "Comanda a fost inregistrata. Vei primi cereri de feedback.")
    return redirect("hardware:cart")


@login_required
def rate_product(request: HttpRequest, product_id: int, rating: int) -> HttpResponse:
    if rating < 1 or rating > 5:
        return HttpResponseBadRequest("Rating invalid. Alege un numar intre 1 si 5.")
    product = get_object_or_404(Product, id=product_id)
    if Nota.objects.filter(user=request.user, product=product).exists():
        messages.info(request, "Ai acordat deja o nota pentru acest produs.")
        return redirect("hardware:product_detail", slug=product.slug)
    Nota.objects.create(user=request.user, product=product, rating=rating)
    FeedbackRequest.objects.filter(user=request.user, product=product).delete()
    messages.success(request, f"Multumim pentru nota {rating} acordata produsului {product.name}.")
    return redirect("hardware:product_detail", slug=product.slug)


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
        suffix = "_urgent" if data.get("urgent") else ""
        payload = {
            "nume": last_name,
            "prenume": first_name or "",
            "varsta": data.get("age_display"),
            "cnp": data.get("cnp", ""),
            "email": data["email"],
            "tip_mesaj": data["message_type"],
            "subiect": data["subject"],
            "minim_zile_asteptare": data["min_wait_days"],
            "mesaj": message_text,
            "urgent": data.get("urgent", False),
            "ip": getattr(self.request, "META", {}).get("REMOTE_ADDR"),
            "moment": timezone.now().isoformat(),
        }
        try:
            file_path = messages_dir / f"mesaj_{timestamp}{suffix}.json"
            with file_path.open("w", encoding="utf-8") as handler:
                json.dump(payload, handler, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.error("Eroare la salvarea mesajului in JSON: %s", exc)
            logger.critical("Salvare mesaj contact esuata pentru %s", data.get("email"))
            send_admin_alert(
                "Eroare la salvarea mesajului de contact",
                "Nu s-a putut salva mesajul de contact in fisier JSON.",
                error_text=str(exc),
            )
            messages.warning(
                self.request,
                "Mesajul a fost salvat, dar fisierul JSON nu a putut fi scris.",
            )

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


def log_view(request: HttpRequest) -> HttpResponse:
    if not _is_site_admin(request.user):
        return render_403(
            request,
            titlu="Eroare acces log",
            mesaj_personalizat="Nu ai voie să accesezi jurnalul de accesări.",
        )
    params = request.GET
    errors: List[str] = []
    info_messages: List[str] = []
    sql_enabled = params.get("sql") == "true"

    queryset = RequestLog.objects.all().order_by("-created_at")
    total_logs = queryset.count()
    messages.debug(request, f"Total accesari inregistrate: {total_logs}")

    limit = None
    ultimele_raw = params.get("ultimele")
    if ultimele_raw not in (None, ""):
        try:
            limit = int(ultimele_raw)
            if limit < 0:
                raise ValueError
        except ValueError:
            errors.append("Parametrul ultimele trebuie să fie un număr întreg pozitiv.")
            limit = None

    accesari_param = params.get("accesari") or params.get("nr")
    accesari_count = None
    accesari_detalii: List[str] = []
    if accesari_param:
        if accesari_param == "nr":
            accesari_count = get_request_count()
        elif accesari_param == "detalii":
            for moment in queryset.values_list("created_at", flat=True):
                accesari_detalii.append(
                    afis_data(moment=timezone.localtime(moment), as_section=False)
                )
        else:
            errors.append("Parametrul accesari poate avea valorile „nr” sau „detalii”.")

    dubluri_raw = params.get("dubluri", "false").lower()
    dubluri = dubluri_raw in ("1", "true", "da", "y", "yes")
    requested_ids: List[int] = []
    bad_ids: List[str] = []
    for raw_value in params.getlist("iduri"):
        for item in raw_value.split(","):
            item = item.strip()
            if not item:
                continue
            try:
                id_val = int(item)
            except ValueError:
                bad_ids.append(item)
                continue
            if dubluri or id_val not in requested_ids:
                requested_ids.append(id_val)
    if bad_ids:
        errors.append(f"Id-urile trebuie să fie numere întregi. Ignorate: {', '.join(bad_ids)}.")

    if requested_ids:
        logs_map = {
            log.id: log for log in RequestLog.objects.filter(id__in=requested_ids)
        }
        missing = [str(i) for i in requested_ids if i not in logs_map]
        if missing:
            errors.append(f"Nu am găsit accesările cu id-urile: {', '.join(missing)}.")
        selected_logs = [logs_map[i] for i in requested_ids if i in logs_map]
    else:
        selected_logs = list(queryset[: limit or total_logs])
        if limit is not None and limit > total_logs:
            errors.append(
                f"Exista doar {total_logs} accesari fata de {limit} accesari cerute"
            )

    accesari_list = [Accesare.from_request_log(log) for log in selected_logs]
    sql_queries = connection.queries if sql_enabled else []
    sql_total = len(sql_queries) * len(accesari_list)

    table_param = params.get("tabel")
    table_columns: List[str] = []
    table_rows: List[List[str]] = []
    column_map = {
        "id": lambda a: a.id,
        "url": lambda a: a.url(),
        "ip": lambda a: a.ip_client,
        "data": lambda a: a.data("%Y-%m-%d %H:%M:%S"),
        "pagina": lambda a: a.pagina(),
    }
    if table_param:
        if table_param == "tot":
            table_columns = list(column_map.keys())
        else:
            requested_cols = [col.strip() for col in table_param.split(",") if col.strip()]
            invalid_cols = [col for col in requested_cols if col not in column_map]
            if invalid_cols:
                errors.append(
                    f"Coloanele {', '.join(invalid_cols)} nu sunt recunoscute. Folosește id, url, ip, data sau pagina."
                )
            table_columns = [col for col in requested_cols if col in column_map]
        if table_columns:
            for accesare in accesari_list:
                table_rows.append([column_map[col](accesare) for col in table_columns])

    path_counts = (
        RequestLog.objects.values("path")
        .annotate(cnt=Count("id"))
        .order_by("cnt", "path")
    )
    least_accessed = path_counts.first()
    most_accessed = path_counts.order_by("-cnt", "path").first()

    context = {
        "titlu": "Jurnal accesări",
        "logs": accesari_list,
        "errors": errors,
        "info_messages": info_messages,
        "accesari_count": accesari_count,
        "accesari_detalii": accesari_detalii,
        "table_columns": table_columns,
        "table_rows": table_rows,
        "least_page": least_accessed["path"] if least_accessed else None,
        "most_page": most_accessed["path"] if most_accessed else None,
        "total_logs": total_logs,
        "sql_enabled": sql_enabled,
        "sql_queries": sql_queries,
        "sql_total": sql_total,
    }
    return render(request, "hardware/log_list.html", context)


def info(request: HttpRequest) -> HttpResponse:
    if not _is_site_admin(request.user):
        return render_403(
            request,
            titlu="Eroare acces info",
            mesaj_personalizat="Nu ai voie să accesezi pagina info.",
        )
    data_param_present = "data" in request.GET
    data_param = request.GET.get("data") if data_param_present else None
    if data_param_present and data_param not in ("", "zi", "timp"):
        mesaj_param = "Parametrul data poate avea valorile „zi”, „timp” sau să fie omis."
        data_section = ""
    else:
        mesaj_param = ""
        data_section = (
            mark_safe(afis_data(data_param or None)) if data_param_present else ""
        )

    parametri = []
    for cheie, valori in request.GET.lists():
        for valoare in valori:
            parametri.append((cheie, valoare))
    messages.debug(request, f"Info page cu {len(parametri)} parametri.")

    context = {
        "titlu": "Informații despre server",
        "heading": "Informații despre server",
        "mesaj_param": mesaj_param,
        "data_section": data_section,
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
