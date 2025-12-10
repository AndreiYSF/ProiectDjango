from __future__ import annotations

from django.conf import settings
from django.db import OperationalError, ProgrammingError

from .models import RequestLog


class RequestLoggingMiddleware:
    """
    Salvează fiecare request într-un model RequestLog pentru rutele publice.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .utils import increment_request_count

        increment_request_count()
        response = self.get_response(request)
        self._log_request(request)
        return response

    def _should_skip(self, request) -> bool:
        path = request.path
        if path.startswith("/admin/"):
            return True
        static_url = getattr(settings, "STATIC_URL", None)
        if static_url and static_url != "/" and path.startswith(static_url):
            return True
        media_url = getattr(settings, "MEDIA_URL", None)
        if media_url and media_url not in ("/", "") and path.startswith(media_url):
            return True
        return False

    def _log_request(self, request) -> None:
        if self._should_skip(request):
            return

        querystring = request.META.get("QUERY_STRING", "")
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = forwarded_for.split(",")[0] if forwarded_for else request.META.get(
            "REMOTE_ADDR"
        )
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        try:
            RequestLog.objects.create(
                path=request.path,
                method=request.method,
                querystring=querystring,
                ip=ip or None,
                user_agent=user_agent,
            )
        except (OperationalError, ProgrammingError):
            # Baza de date nu este pregătită (ex: înainte de migrații). Ignorăm.
            pass
