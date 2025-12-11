from __future__ import annotations

import re
from datetime import date

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


PHONE_PATTERN = re.compile(r"^[0-9+\-\s]{7,20}$")


class RegistrationForm(UserCreationForm):
    phone = forms.CharField(
        label="Telefon",
        max_length=20,
        required=False,
        help_text="Acceptat: cifre, +, -, spații (minim 7 caractere).",
    )
    country = forms.CharField(label="Țară", max_length=50)
    county = forms.CharField(label="Județ", max_length=50)
    city = forms.CharField(label="Oraș", max_length=50)
    street = forms.CharField(label="Stradă", max_length=120)
    birth_date = forms.DateField(
        label="Data nașterii",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    remember_me = forms.BooleanField(
        label="Rămâi autentificat 1 zi",
        required=False,
        initial=True,
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "country",
            "county",
            "city",
            "street",
            "birth_date",
            "newsletter_opt_in",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_order = [
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "country",
            "county",
            "city",
            "street",
            "birth_date",
            "newsletter_opt_in",
            "password1",
            "password2",
            "remember_me",
        ]

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if phone and not PHONE_PATTERN.fullmatch(phone):
            raise forms.ValidationError(
                "Telefonul poate conține doar cifre, spații, + sau -, minim 7 caractere."
            )
        return phone

    def clean_birth_date(self):
        bdate = self.cleaned_data.get("birth_date")
        if bdate:
            today = timezone.localdate()
            if bdate > today:
                raise forms.ValidationError("Data nașterii nu poate fi în viitor.")
            years = today.year - bdate.year - (
                (today.month, today.day) < (bdate.month, bdate.day)
            )
            if years < 14:
                raise forms.ValidationError("Trebuie să ai cel puțin 14 ani pentru a te înregistra.")
        return bdate

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Există deja un cont cu acest e-mail.")
        return email

    def clean_street(self):
        street = self.cleaned_data.get("street", "").strip()
        if len(street) < 3:
            raise forms.ValidationError("Strada trebuie să aibă minim 3 caractere.")
        return street


class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(
        label="Ține-mă minte 1 zi",
        required=False,
        initial=True,
    )
