from __future__ import annotations

from collections import Counter
from typing import List, Optional
from urllib.parse import urlencode

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone


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


def afis_data(mode: Optional[str] = None, moment=None) -> str:
    """
    Returnează data și/sau ora într-un format prietenos în limba română.
    mode poate fi None, 'zi' sau 'timp'.
    """
    moment = moment or timezone.localtime()
    zi = f"{ROMANIAN_DAYS[moment.weekday()]}, {moment.day} {ROMANIAN_MONTHS[moment.month - 1]} {moment.year}"
    ora = moment.strftime("%H:%M:%S")

    if mode == "zi":
        return zi
    if mode == "timp":
        return ora
    return f"{zi} {ora}"


class Accesare:
    """
    Reține informații despre accesarea unei pagini pentru a fi afișate în /log.
    """

    _auto_id = 1

    def __init__(self, request: HttpRequest):
        self.id = Accesare._auto_id
        Accesare._auto_id += 1

        self.ip_client = request.META.get("REMOTE_ADDR", "necunoscut")
        self._path = request.path
        self._timestamp = timezone.localtime()
        self._method = request.method
        # păstrăm valorile în ordinea primită, incluzând duplicatele
        self._query_items = [
            (key, value) for key, values in request.GET.lists() for value in values
        ]

    def lista_parametri(self) -> List[tuple[str, str]]:
        return list(self._query_items)

    def url(self) -> str:
        if not self._query_items:
            return self._path
        return f"{self._path}?{urlencode(self._query_items, doseq=True)}"

    def data(self, fmt: Optional[str] = None) -> str:
        if fmt in (None, "zi", "timp"):
            return afis_data(fmt, self._timestamp)
        try:
            return self._timestamp.strftime(fmt)
        except (TypeError, ValueError):
            return self._timestamp.isoformat()

    def pagina(self) -> str:
        return self._path

    @property
    def method(self) -> str:
        return self._method


accesari_log: List[Accesare] = []


def _log_request(request: HttpRequest) -> Accesare:
    accesare = Accesare(request)
    accesari_log.append(accesare)
    return accesare


def home(request: HttpRequest) -> HttpResponse:
    _log_request(request)

    context = {
        "sectiuni": [
            {
                "titlu": "Produse populare",
                "descriere": (
                    "Descoperă bormașinile, șurubelnițele electrice și accesoriile "
                    "preferate de profesioniști și pasionați de bricolaj."
                ),
            },
            {
                "titlu": "Branduri partenere",
                "descriere": (
                    "Colaborăm cu mărci precum Bosch, DeWalt, Makita sau Black+Decker "
                    "pentru a-ți livra scule de încredere."
                ),
            },
            {
                "titlu": "Promoții curente",
                "descriere": (
                    "Oferta se actualizează săptămânal cu pachete de accesorii și "
                    "discount-uri la colecțiile de sezon."
                ),
            },
        ],
    }
    return render(request, "hardware/index.html", context)


def despre(request: HttpRequest) -> HttpResponse:
    _log_request(request)
    context = {
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
    return render(request, "hardware/despre.html", context)


def info(request: HttpRequest) -> HttpResponse:
    accesare = _log_request(request)

    data_param = request.GET.get("data")
    if data_param not in (None, "zi", "timp", ""):
        # parametru nevalid → îl tratăm ca None dar trimitem mesaj
        data_param = None
        mesaj_param = "Parametrul data poate avea valorile „zi”, „timp” sau să fie omis."
    else:
        mesaj_param = ""

    context = {
        "titlu": "Informații despre server",
        "heading": "Informații despre server",
        "mesaj_param": mesaj_param,
        "moment": afis_data(data_param or None),
        "parametri": accesare.lista_parametri(),
        "server_info": [
            ("Adresă IP client", accesare.ip_client),
            ("Metodă HTTP", accesare.method),
            ("URL accesat", accesare.url()),
            ("User-Agent", request.META.get("HTTP_USER_AGENT", "necunoscut")),
            ("Host", request.get_host()),
        ],
    }
    return render(request, "hardware/info.html", context)


def log(request: HttpRequest) -> HttpResponse:
    _log_request(request)

    errors: List[str] = []
    messages: List[str] = []
    query = request.GET

    total_accesari = len(accesari_log)

    ultimele_param = query.get("ultimele")
    ultimele_accesari: Optional[List[Accesare]] = None
    if ultimele_param is not None:
        try:
            n = int(ultimele_param)
            if n <= 0:
                errors.append("Parametrul ultimele trebuie să fie un număr pozitiv.")
            else:
                if n > total_accesari:
                    messages.append(
                        f"Există doar {total_accesari} accesări față de {n} accesări cerute."
                    )
                    ultimele_accesari = accesari_log.copy()
                else:
                    ultimele_accesari = accesari_log[-n:]
        except ValueError:
            errors.append("Parametrul ultimele trebuie să fie un număr întreg.")

    accesari_param = query.get("accesari")
    accesari_detalii: List[str] = []
    if accesari_param:
        if accesari_param == "nr":
            messages.append(
                f"Numărul total de accesări de la pornirea serverului este {total_accesari}."
            )
        elif accesari_param == "detalii":
            accesari_detalii = [entry.data() for entry in accesari_log]
        else:
            errors.append(
                "Parametrul accesari acceptă valorile „nr” sau „detalii”."
            )

    iduri_valori = query.getlist("iduri")
    dubluri_param = query.get("dubluri", "false").lower() == "true"
    accesari_din_iduri: List[Accesare] = []
    if iduri_valori:
        valori: List[int] = []
        iduri_invalide: List[str] = []
        for raw in iduri_valori:
            for item in raw.split(","):
                item = item.strip()
                if not item:
                    continue
                try:
                    valori.append(int(item))
                except ValueError:
                    iduri_invalide.append(item)
        if iduri_invalide:
            errors.append(
                "Id-urile următoare nu sunt valide: " + ", ".join(iduri_invalide)
            )
        if valori:
            if not dubluri_param:
                seen = set()
                valori = [v for v in valori if not (v in seen or seen.add(v))]
            accesari_map = {entry.id: entry for entry in accesari_log}
            missing = []
            for ident in valori:
                entry = accesari_map.get(ident)
                if entry:
                    accesari_din_iduri.append(entry)
                else:
                    missing.append(str(ident))
            if missing:
                errors.append(
                    "Accesările cu id-urile următoare nu au fost găsite: "
                    + ", ".join(missing)
                )

    tabel_param = query.get("tabel")
    tabel_coloane: List[str] = []
    tabel_linii: List[List[str]] = []
    coloane_disponibile = {
        "id": lambda acc: str(acc.id),
        "ip_client": lambda acc: acc.ip_client,
        "url": lambda acc: acc.url(),
        "data": lambda acc: acc.data(),
        "pagina": lambda acc: acc.pagina(),
        "metoda": lambda acc: acc.method,
        "parametri": lambda acc: ", ".join(
            f"{k}={v}" for k, v in acc.lista_parametri()
        )
        or "-",
    }

    if tabel_param:
        if tabel_param == "tot":
            tabel_coloane = list(coloane_disponibile.keys())
        else:
            solicitare = [col.strip() for col in tabel_param.split(",") if col.strip()]
            coloane_invalide = [
                col for col in solicitare if col not in coloane_disponibile
            ]
            if coloane_invalide:
                errors.append(
                    "Coloane necunoscute pentru tabel: " + ", ".join(coloane_invalide)
                )
            else:
                tabel_coloane = solicitare
        if tabel_coloane:
            for entry in accesari_log:
                tabel_linii.append(
                    [coloane_disponibile[col](entry) for col in tabel_coloane]
                )

    counts = Counter(entry.pagina() for entry in accesari_log)
    pagina_min = pagina_max = ""
    if counts:
        min_count = min(counts.values())
        max_count = max(counts.values())
        pagina_min = sorted(
            [pagina for pagina, cnt in counts.items() if cnt == min_count]
        )[0]
        pagina_max = sorted(
            [pagina for pagina, cnt in counts.items() if cnt == max_count]
        )[0]

    context = {
        "errors": errors,
        "messages": messages,
        "ultimele_accesari": ultimele_accesari,
        "accesari_detalii": accesari_detalii,
        "accesari_din_iduri": accesari_din_iduri,
        "tabel_coloane": tabel_coloane,
        "tabel_linii": tabel_linii,
        "pagina_min": pagina_min,
        "pagina_max": pagina_max,
        "total_accesari": total_accesari,
        "log": accesari_log,
        "dubluri": dubluri_param,
    }
    return render(request, "hardware/log.html", context)


def in_lucru(request: HttpRequest, page_title: str) -> HttpResponse:
    _log_request(request)
    context = {"page_title": page_title}
    return render(request, "hardware/in_lucru.html", context)
