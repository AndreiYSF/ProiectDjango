from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.utils import timezone
from django.utils.text import slugify

from .models import Brand, Category, Material, Product


TEXT_PATTERN = re.compile(r"^[A-Za-zĂÂÎȘȚăâîșț ]+$")


def validate_capitalized_text(value: str, allow_empty: bool = False) -> str:
    if not value:
        if allow_empty:
            return ""
        raise forms.ValidationError("Completați acest câmp.")
    cleaned = value.strip()
    if not cleaned:
        if allow_empty:
            return ""
        raise forms.ValidationError("Completați acest câmp.")
    if not cleaned[0].isalpha() or not cleaned[0].isupper():
        raise forms.ValidationError("Textul trebuie să înceapă cu literă mare.")
    if not TEXT_PATTERN.fullmatch(cleaned):
        raise forms.ValidationError("Textul poate conține doar litere și spații.")
    return cleaned


class ProductFilterForm(forms.Form):
    DEFAULT_PER_PAGE = 10
    PER_PAGE_CHOICES = [
        (5, "5"),
        (10, "10"),
        (20, "20"),
        (50, "50"),
    ]

    name = forms.CharField(label="Nume produs", required=False)
    slug = forms.CharField(label="Slug", required=False)
    description = forms.CharField(label="Descriere conține", required=False)
    category = forms.ModelChoiceField(
        label="Categorie",
        queryset=Category.objects.none(),
        required=False,
    )
    brand = forms.ModelChoiceField(
        label="Brand",
        queryset=Brand.objects.none(),
        required=False,
    )
    materials = forms.ModelMultipleChoiceField(
        label="Materiale",
        queryset=Material.objects.none(),
        required=False,
    )
    available = forms.ChoiceField(
        label="Disponibilitate",
        choices=[
            ("", "Toate"),
            ("true", "Doar disponibile"),
            ("false", "Doar indisponibile"),
        ],
        required=False,
    )
    condition = forms.ChoiceField(
        label="Condiție",
        choices=[("", "Toate")] + list(Product.Condition.choices),
        required=False,
    )
    price_min = forms.DecimalField(
        label="Preț minim",
        required=False,
        min_value=0,
        decimal_places=2,
    )
    price_max = forms.DecimalField(
        label="Preț maxim",
        required=False,
        min_value=0,
        decimal_places=2,
    )
    price = forms.DecimalField(
        label="Preț exact",
        required=False,
        min_value=0,
        decimal_places=2,
    )
    stock_min = forms.IntegerField(
        label="Stoc minim",
        required=False,
        min_value=0,
    )
    stock_max = forms.IntegerField(
        label="Stoc maxim",
        required=False,
        min_value=0,
    )
    stock = forms.IntegerField(
        label="Stoc exact",
        required=False,
        min_value=0,
    )
    added_after = forms.DateField(
        label="Adăugat după",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    added_before = forms.DateField(
        label="Adăugat înainte",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    updated_after = forms.DateField(
        label="Actualizat după",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    updated_before = forms.DateField(
        label="Actualizat înainte",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    per_page = forms.TypedChoiceField(
        label="Elemente pe pagină",
        choices=PER_PAGE_CHOICES,
        required=False,
        coerce=int,
        empty_value=DEFAULT_PER_PAGE,
    )

    def __init__(
        self,
        *args,
        category_queryset=None,
        brand_queryset=None,
        material_queryset=None,
        lock_category=False,
        category_instance=None,
        **kwargs,
    ) -> None:
        self.lock_category = lock_category
        self.category_instance = category_instance
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = category_queryset or Category.objects.order_by(
            "name"
        )
        self.fields["brand"].queryset = brand_queryset or Brand.objects.order_by("name")
        self.fields["materials"].queryset = (
            material_queryset or Material.objects.order_by("name")
        )
        if lock_category and category_instance is not None:
            self.fields["category"].initial = category_instance.pk
            self.fields["category"].widget = forms.HiddenInput()
            self.fields["category"].widget.attrs["readonly"] = "readonly"
        self.altered_category = False

    def clean_name(self):
        value = self.cleaned_data.get("name")
        if value and len(value.strip()) < 3:
            raise forms.ValidationError(
                "Introduceți cel puțin 3 caractere pentru numele produsului."
            )
        return value

    def clean_slug(self):
        value = self.cleaned_data.get("slug")
        if value and len(value) < 3:
            raise forms.ValidationError(
                "Slug-ul trebuie să conțină minimum 3 caractere."
            )
        return value

    def clean_price_min(self):
        value = self.cleaned_data.get("price_min")
        if value is not None and value < 0:
            raise forms.ValidationError("Prețul minim trebuie să fie pozitiv.")
        return value

    def clean_price_max(self):
        value = self.cleaned_data.get("price_max")
        if value is not None and value < 0:
            raise forms.ValidationError("Prețul maxim trebuie să fie pozitiv.")
        return value

    def clean(self):
        cleaned_data = super().clean()
        price_min = cleaned_data.get("price_min")
        price_max = cleaned_data.get("price_max")
        if price_min is not None and price_max is not None and price_min > price_max:
            self.add_error(
                "price_max",
                "Prețul maxim trebuie să fie mai mare sau egal cu prețul minim.",
            )
        stock_min = cleaned_data.get("stock_min")
        stock_max = cleaned_data.get("stock_max")
        if stock_min is not None and stock_max is not None and stock_min > stock_max:
            self.add_error(
                "stock_max",
                "Stocul maxim trebuie să fie mai mare sau egal cu stocul minim.",
            )
        if self.lock_category and self.category_instance is not None:
            category = cleaned_data.get("category")
            if category and category.pk != self.category_instance.pk:
                self.altered_category = True
                self.add_error(
                    "category",
                    "Categoria selectată nu poate fi modificată din această pagină.",
                )
                cleaned_data["category"] = self.category_instance
            elif category is None:
                cleaned_data["category"] = self.category_instance
        return cleaned_data


class ContactForm(forms.Form):
    MESSAGE_CHOICES = [
        ("reclamatie", "Reclamație"),
        ("intrebare", "Întrebare"),
        ("review", "Review"),
        ("cerere", "Cerere"),
        ("programare", "Programare"),
    ]

    last_name = forms.CharField(label="Nume", max_length=10)
    first_name = forms.CharField(label="Prenume", max_length=30, required=False)
    birth_date = forms.DateField(
        label="Data nașterii",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    email = forms.EmailField(label="E-mail")
    confirm_email = forms.EmailField(label="Confirmare e-mail")
    message_type = forms.ChoiceField(label="Tip mesaj", choices=MESSAGE_CHOICES)
    subject = forms.CharField(label="Subiect", max_length=120)
    min_wait_days = forms.IntegerField(
        label="Minim zile așteptare",
        min_value=1,
        error_messages={
            "min_value": "Introduceți o valoare pozitivă pentru zilele de așteptare.",
            "invalid": "Introduceți un număr întreg pentru zilele de așteptare.",
        },
    )
    message = forms.CharField(
        label="Mesaj (vă rugăm să vă semnați la final)",
        widget=forms.Textarea,
    )

    def clean_last_name(self):
        return validate_capitalized_text(self.cleaned_data.get("last_name"))

    def clean_first_name(self):
        return validate_capitalized_text(
            self.cleaned_data.get("first_name"), allow_empty=True
        )

    def clean_subject(self):
        return validate_capitalized_text(self.cleaned_data.get("subject"))

    def clean_message(self):
        message = self.cleaned_data.get("message", "")
        if re.search(r"https?://", message, re.IGNORECASE):
            raise forms.ValidationError(
                "Mesajul nu poate conține linkuri care încep cu http:// sau https://."
            )
        words = re.findall(r"\w+", message, flags=re.UNICODE)
        if not 5 <= len(words) <= 100:
            raise forms.ValidationError(
                "Mesajul trebuie să conțină între 5 și 100 de cuvinte."
            )
        last_name = self.cleaned_data.get("last_name")
        if last_name and words:
            if words[-1].casefold() != last_name.strip().casefold():
                raise forms.ValidationError(
                    "Ultimul cuvânt din mesaj trebuie să fie numele completat în formular."
                )
        return message

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        confirm_email = cleaned_data.get("confirm_email")
        if email and confirm_email and email != confirm_email:
            self.add_error(
                "confirm_email", "Adresele de e-mail trebuie să coincidă."
            )
        birth_date = cleaned_data.get("birth_date")
        if birth_date:
            today = timezone.localdate()
            if birth_date > today:
                self.add_error("birth_date", "Data nașterii nu poate fi în viitor.")
            else:
                years = today.year - birth_date.year
                if (today.month, today.day) < (birth_date.month, birth_date.day):
                    years -= 1
                if years < 18:
                    self.add_error(
                        "birth_date",
                        "Expeditorul trebuie să aibă cel puțin 18 ani.",
                    )
        return cleaned_data

    def normalized_data(self):
        data = self.cleaned_data.copy()
        message = data.get("message", "")
        message = re.sub(r"\s+", " ", message.replace("\n", " ")).strip()
        data["message"] = message
        birth_date = data.get("birth_date")
        if birth_date:
            today = timezone.localdate()
            years = today.year - birth_date.year
            months = today.month - birth_date.month
            if today.day < birth_date.day:
                months -= 1
            if months < 0:
                months += 12
                years -= 1
            data["age_display"] = f"{years} ani și {months} luni"
        data.pop("confirm_email", None)
        if "birth_date" in data:
            data.pop("birth_date")
        return data


class ProductCreateForm(forms.ModelForm):
    base_price = forms.DecimalField(
        label="Preț de bază",
        min_value=Decimal("0.01"),
        decimal_places=2,
        help_text="Introduceți valoarea fără TVA.",
    )
    markup_percentage = forms.DecimalField(
        label="Adaos procentual",
        min_value=Decimal("0"),
        max_value=Decimal("500"),
        decimal_places=2,
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "brand",
            "description",
            "stock",
            "available",
            "condition",
            "materials",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "name": "Nume produs",
            "category": "Categorie",
            "brand": "Brand",
            "description": "Descriere",
            "stock": "Stoc inițial",
            "available": "Disponibil",
            "condition": "Condiție",
            "materials": "Materiale",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["materials"].queryset = Material.objects.order_by("name")

    def clean_name(self):
        name = self.cleaned_data.get("name", "")
        if len(name.strip()) < 5:
            raise forms.ValidationError(
                "Numele produsului trebuie să conțină cel puțin 5 caractere."
            )
        return name

    def clean_description(self):
        description = self.cleaned_data.get("description", "")
        if description and len(description.strip()) < 20:
            raise forms.ValidationError(
                "Descrierea trebuie să aibă cel puțin 20 de caractere dacă este completată."
            )
        return description

    def clean_markup_percentage(self):
        markup = self.cleaned_data.get("markup_percentage")
        if markup is not None and markup > Decimal("500"):
            raise forms.ValidationError(
                "Adaosul procentual nu poate depăși 500%."
            )
        return markup

    def clean(self):
        cleaned_data = super().clean()
        base_price = cleaned_data.get("base_price")
        markup = cleaned_data.get("markup_percentage")
        if base_price is not None and markup is not None:
            final_price = base_price * (Decimal("1") + markup / Decimal("100"))
            if final_price < Decimal("10"):
                self.add_error(
                    "base_price",
                    "Prețul final trebuie să fie de cel puțin 10 lei.",
                )
            self.computed_price = final_price.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        return cleaned_data

    def _generate_unique_slug(self, name: str) -> str:
        base_slug = slugify(name) or "produs"
        slug = base_slug
        suffix = 2
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        return slug

    def save(self, commit: bool = True):
        instance = super().save(commit=False)
        final_price = getattr(
            self, "computed_price", Decimal(self.cleaned_data["base_price"])
        )
        instance.price = final_price
        if not instance.slug:
            instance.slug = self._generate_unique_slug(instance.name)
        if commit:
            instance.save()
            self.save_m2m()
        return instance
