from __future__ import annotations

from typing import Any, Dict
import logging
import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import Permission
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.contrib.auth.views import PasswordChangeView
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView

from .forms import LoginForm, RegistrationForm
from .models import User
from .utils import send_admin_alert


logger = logging.getLogger("django")
LOGIN_FAIL_LIMIT = 3
LOGIN_FAIL_WINDOW = 120


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
    success_url = reverse_lazy("accounts:login")

    def _build_confirm_url(self, code: str) -> str:
        path = reverse("confirm_email", kwargs={"code": code})
        return self.request.build_absolute_uri(path)

    def _send_confirmation_email(self, user: User) -> None:
        confirm_url = self._build_confirm_url(user.cod)
        logo_url = self.request.build_absolute_uri(static("hardware/img/toolbox.svg"))
        context = {
            "user": user,
            "confirm_url": confirm_url,
            "logo_url": logo_url,
        }
        subject = "Confirmare e-mail"
        text_body = render_to_string("accounts/email_confirmation.txt", context)
        html_body = render_to_string("accounts/email_confirmation.html", context)
        sender = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
        email = EmailMultiAlternatives(subject, text_body, sender, [user.email])
        email.attach_alternative(html_body, "text/html")
        email.send()

    def form_valid(self, form: RegistrationForm) -> HttpResponse:
        user = form.save(commit=False)
        user.email_confirmat = False
        user.cod = secrets.token_urlsafe(32)
        user.save()
        try:
            form.save_m2m()
        except AttributeError:
            pass
        try:
            self._send_confirmation_email(user)
            messages.success(
                self.request,
                "Cont creat. Verifică e-mailul pentru confirmare.",
            )
            logger.info("Email de confirmare trimis pentru user %s", user.username)
        except Exception as exc:
            logger.error("Eroare la trimiterea confirmarii email: %s", exc)
            logger.critical("Confirmare email esuata pentru user %s", user.username)
            messages.warning(
                self.request,
                "Cont creat, dar nu am putut trimite e-mailul de confirmare.",
            )
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

    def form_invalid(self, form: LoginForm) -> HttpResponse:
        username = self.request.POST.get("username", "").strip()
        ip = _get_client_ip(self.request)
        if username:
            cache_key = f"login_fail:{username}:{ip}"
            count = (cache.get(cache_key) or 0) + 1
            cache.set(cache_key, count, timeout=LOGIN_FAIL_WINDOW)
            logger.warning("Autentificare esuata pentru %s (incercare %s)", username, count)
            if count == LOGIN_FAIL_LIMIT:
                send_admin_alert(
                    "Logari suspecte",
                    f"3 logari esuate in 2 minute pentru username {username}, IP {ip}",
                )
        return super().form_invalid(form)


class LogoutView(DjangoLogoutView):
    next_page = reverse_lazy("hardware:home")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.user.is_authenticated:
            perm = Permission.objects.filter(codename="vizualizeaza_oferta").first()
            if perm:
                request.user.user_permissions.remove(perm)
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


def _get_client_ip(request: HttpRequest) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def confirm_email(request: HttpRequest, code: str) -> HttpResponse:
    user = User.objects.filter(cod=code).first()
    if not user:
        logger.warning("Cod confirmare invalid: %s", code)
        context = {"success": False, "message": "Cod invalid sau expirat."}
        return render(request, "accounts/confirm_email_result.html", context)

    user.email_confirmat = True
    user.cod = None
    user.save(update_fields=["email_confirmat", "cod"])
    logger.info("Email confirmat pentru user %s", user.username)
    context = {"success": True, "message": "E-mail confirmat cu succes."}
    return render(request, "accounts/confirm_email_result.html", context)
