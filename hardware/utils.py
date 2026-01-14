from __future__ import annotations

from datetime import datetime
from typing import List, Tuple
from urllib.parse import parse_qsl

from django.utils import timezone


_REQUEST_COUNT = 0


class _CallableUrl(str):
    def __call__(self) -> str:
        return str(self)


class _CallableDate(datetime):
    def __new__(cls, value: datetime):
        return datetime.__new__(
            cls,
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            value.tzinfo,
            getattr(value, "fold", 0),
        )

    def __call__(self, format_str: str | None = None):
        if format_str:
            return self.strftime(format_str)
        return self


def increment_request_count() -> None:
    global _REQUEST_COUNT
    _REQUEST_COUNT += 1


def get_request_count() -> int:
    return _REQUEST_COUNT


class Accesare:
    """
    Reprezintă o accesare din RequestLog într-un obiect simplu folosit în /log.
    """

    _auto_id = 0

    def __init__(
        self,
        ip_client: str,
        path: str,
        querystring: str = "",
        created_at: datetime | None = None,
        id: int | None = None,
    ) -> None:
        if id is None:
            Accesare._auto_id += 1
            self.id = Accesare._auto_id
        else:
            self.id = id
            Accesare._auto_id = max(Accesare._auto_id, id)

        self.ip_client = ip_client or "necunoscut"
        self.path = path or "/"
        self.querystring = querystring or ""
        self.created_at = created_at or timezone.localtime()

    @classmethod
    def from_request_log(cls, log) -> "Accesare":
        return cls(
            ip_client=getattr(log, "ip", "") or "necunoscut",
            path=getattr(log, "path", "/"),
            querystring=getattr(log, "querystring", ""),
            created_at=getattr(log, "created_at", None),
            id=getattr(log, "id", None),
        )

    def lista_parametri(self) -> List[Tuple[str, str | None]]:
        params = parse_qsl(self.querystring, keep_blank_values=True)
        return [(nume, valoare or None) for nume, valoare in params]

    def _build_url(self) -> str:
        if self.querystring:
            return f"{self.path}?{self.querystring}"
        return self.path

    @property
    def url(self) -> str:
        return _CallableUrl(self._build_url())

    @property
    def data(self) -> datetime:
        return _CallableDate(self.created_at)

    def pagina(self) -> str:
        return self.path or "/"


def get_ip(request) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR")
