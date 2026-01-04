from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=50, blank=True)
    county = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    street = models.CharField(max_length=120, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    newsletter_opt_in = models.BooleanField(default=False)
    cod = models.CharField(max_length=100, null=True, blank=True)
    email_confirmat = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def age(self) -> str | None:
        if not self.birth_date:
            return None
        today = timezone.localdate()
        years = today.year - self.birth_date.year
        months = today.month - self.birth_date.month
        if today.day < self.birth_date.day:
            months -= 1
        if months < 0:
            months += 12
            years -= 1
        return f"{years} ani și {months} luni"

    def __str__(self) -> str:
        return self.get_full_name() or self.username
