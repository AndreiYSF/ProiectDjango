from __future__ import annotations

from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.contrib.auth.views import PasswordChangeView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from .forms import LoginForm, RegistrationForm
from .models import User


def store_profile_in_session(request: HttpRequest, user: User) -> None:
    request.session["profile_data"] = {
        "username": user.username,
        "email": user.email,
        "nume": user.last_name,
        "prenume": user.first_name,
        "telefon": user.phone,
        "tara": user.country,
        "judet": user.county,
        "oras": user.city,
        "strada": user.street,
        "varsta": user.age(),
        "newsletter": user.newsletter_opt_in,
    }


class RegistrationView(FormView):
    template_name = "accounts/register.html"
    form_class = RegistrationForm
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form: RegistrationForm) -> HttpResponse:
        user = form.save()
        login(self.request, user)
        store_profile_in_session(self.request, user)
        if form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(86400)
        else:
            self.request.session.set_expiry(0)
        messages.success(self.request, "Cont creat cu succes.")
        return super().form_valid(form)


class LoginView(DjangoLoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm

    def form_valid(self, form: LoginForm) -> HttpResponse:
        response = super().form_valid(form)
        user = self.request.user
        store_profile_in_session(self.request, user)
        remember = form.cleaned_data.get("remember_me")
        if remember:
            self.request.session.set_expiry(86400)
        else:
            self.request.session.set_expiry(0)
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("accounts:profile")


class LogoutView(DjangoLogoutView):
    next_page = reverse_lazy("hardware:home")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        logout(request)
        messages.info(request, "Te-ai deconectat.")
        return redirect(self.next_page)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        profile_data = self.request.session.get("profile_data", {})
        context["profile_data"] = profile_data
        return context


class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(self.request, "Parola a fost schimbată.")
        return super().form_valid(form)
