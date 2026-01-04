from __future__ import annotations

import logging
from datetime import datetime, timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import FeedbackRequest, Nota, Purchase


logger = logging.getLogger("django")


def _add_month(dt: datetime) -> datetime:
    year = dt.year + (dt.month // 12)
    month = dt.month % 12 + 1
    day = dt.day
    last_day = _last_day_of_month(year, month)
    if day > last_day:
        day = last_day
    return dt.replace(year=year, month=month, day=day)


def _last_day_of_month(year: int, month: int) -> int:
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day


@receiver(post_save, sender=Purchase)
def schedule_feedback_request(sender, instance: Purchase, created: bool, **kwargs) -> None:
    if not created:
        return
    if Nota.objects.filter(user=instance.user, product=instance.product).exists():
        logger.info(
            "Userul %s a dat deja nota pentru %s; nu programam feedback.",
            instance.user.username,
            instance.product.name,
        )
        return
    next_send_at = _add_month(instance.purchased_at)
    FeedbackRequest.objects.get_or_create(
        user=instance.user,
        product=instance.product,
        defaults={"next_send_at": next_send_at},
    )
