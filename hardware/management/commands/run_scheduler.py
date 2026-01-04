import random
import time
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
import logging

from accounts.models import User
from hardware.models import FeedbackRequest, Nota, Product, Promotion, RequestLog


DAY_MAP = {
    "luni": 0,
    "marti": 1,
    "miercuri": 2,
    "joi": 3,
    "vineri": 4,
    "sambata": 5,
    "duminica": 6,
}


logger = logging.getLogger("django")


class Command(BaseCommand):
    help = "Ruleaza taskurile programate pentru laborator."

    def handle(self, *args, **options):
        last_run = {
            "cleanup_unconfirmed": None,
            "cleanup_logs": None,
            "newsletter": None,
            "promo_cleanup": None,
            "feedback": None,
        }

        self.stdout.write(self.style.SUCCESS("Scheduler pornit."))
        while True:
            now = timezone.localtime()

            if _should_run_every(
                now,
                last_run["cleanup_unconfirmed"],
                settings.CLEANUP_UNCONFIRMED_MINUTES,
            ):
                cleanup_unconfirmed_users(now)
                last_run["cleanup_unconfirmed"] = now

            if _should_run_every(
                now,
                last_run["cleanup_logs"],
                settings.LOG_CLEANUP_INTERVAL_MINUTES,
            ):
                cleanup_request_logs(now)
                last_run["cleanup_logs"] = now

            if _should_run_weekly(
                now,
                last_run["newsletter"],
                settings.NEWSLETTER_DAY,
                settings.NEWSLETTER_HOUR,
            ):
                send_weekly_newsletter(now)
                last_run["newsletter"] = now

            if _should_run_weekly(
                now,
                last_run["promo_cleanup"],
                settings.PROMO_CLEANUP_DAY,
                settings.PROMO_CLEANUP_HOUR,
            ):
                cleanup_expired_promotions(now)
                last_run["promo_cleanup"] = now

            if _should_run_every(
                now,
                last_run["feedback"],
                settings.FEEDBACK_CHECK_INTERVAL_MINUTES,
            ):
                send_feedback_requests(now)
                last_run["feedback"] = now

            time.sleep(30)


def _should_run_every(now, last_run, minutes):
    if minutes <= 0:
        return False
    if last_run is None:
        return True
    delta = now - last_run
    return delta.total_seconds() >= minutes * 60


def _should_run_weekly(now, last_run, day_name, hour):
    day_index = DAY_MAP.get(str(day_name).lower())
    if day_index is None:
        return False
    if now.weekday() != day_index or now.hour != int(hour):
        return False
    if last_run is None:
        return True
    return last_run.date() != now.date()


def cleanup_unconfirmed_users(now):
    threshold = now - timedelta(minutes=settings.CLEANUP_UNCONFIRMED_MINUTES)
    users = User.objects.filter(email_confirmat=False, date_joined__lte=threshold)
    count = users.count()
    for user in users:
        logger.warning("Stergere user neconfirmat: %s (%s)", user.username, user.email)
        user.delete()
    if count:
        logger.info("Total useri neconfirmati stersi: %s", count)


def send_weekly_newsletter(now):
    threshold = now - timedelta(minutes=settings.NEWSLETTER_MIN_AGE_MINUTES)
    users = (
        User.objects.filter(email_confirmat=True, date_joined__lte=threshold)
        .exclude(email="")
    )
    if not users.exists():
        logger.info("Nu exista utilizatori eligibili pentru newsletter.")
        return

    tips = [
        "Verifica sculele noi din categoria scule electrice.",
        "Nu uita de echipamentele de protectie pentru proiectele DIY.",
        "Cele mai vandute produse sunt actualizate in catalog.",
        "Incearca un tutorial nou pentru imbunatatirea abilitatilor.",
    ]
    products = list(Product.objects.values_list("name", flat=True))
    sender = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")

    for user in users:
        tip = random.choice(tips)
        produs = random.choice(products) if products else "produsele recomandate"
        subject = f"Newsletter Magazin Hardware - {now:%d.%m.%Y}"
        body = (
            f"Salut, {user.first_name or user.username}!\n\n"
            f"{tip}\n"
            f"Recomandarea zilei: {produs}.\n\n"
            "Multumim ca esti alaturi de noi!"
        )
        send_mail(subject, body, sender, [user.email])
    logger.info("Newsletter trimis catre %s utilizatori.", users.count())


def cleanup_request_logs(now):
    threshold = now - timedelta(days=settings.REQUESTLOG_RETENTION_DAYS)
    logs = RequestLog.objects.filter(created_at__lt=threshold)
    count = logs.count()
    if count:
        logs.delete()
        logger.info("Sterse %s loguri mai vechi de %s zile.", count, settings.REQUESTLOG_RETENTION_DAYS)


def cleanup_expired_promotions(now):
    promos = Promotion.objects.filter(expires_at__lt=now.date())
    count = promos.count()
    if count:
        promos.delete()
        logger.info("Sterse %s promotii expirate.", count)


def send_feedback_requests(now):
    due = FeedbackRequest.objects.filter(next_send_at__lte=now)
    if not due.exists():
        return
    base_url = settings.SITE_URL.rstrip("/")
    sender = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")

    for request_item in due:
        if Nota.objects.filter(user=request_item.user, product=request_item.product).exists():
            request_item.delete()
            continue
        if not request_item.user.email:
            continue
        rating_links = []
        for rating in range(1, 6):
            url = f"{base_url}{reverse('hardware:rate_product', args=[request_item.product.id, rating])}"
            rating_links.append({"rating": rating, "url": url})

        context = {
            "user": request_item.user,
            "product": request_item.product,
            "rating_links": rating_links,
        }
        subject = f"Feedback pentru {request_item.product.name}"
        text_body = render_to_string("hardware/emails/feedback_request.txt", context)
        html_body = render_to_string("hardware/emails/feedback_request.html", context)
        email = EmailMultiAlternatives(subject, text_body, sender, [request_item.user.email])
        email.attach_alternative(html_body, "text/html")
        email.send()
        request_item.next_send_at = _add_month(request_item.next_send_at)
        request_item.save(update_fields=["next_send_at"])


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
