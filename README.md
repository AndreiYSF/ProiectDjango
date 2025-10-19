# Magazin Hardware – Proiect Django

Aplicație Django 5.2 (limbă `ro-RO`, fus orar `Europe/Bucharest`) pentru un magazin de scule și accesorii. Include catalog de produse cu filtre și sortări, tutoriale video, formular de contact, coș de cumpărături bazat pe sesiune și un jurnal de accesări persistent în baza de date. Aplicația „core” expune și o secțiune de blog experimentală.

## Cerințe preliminare

- Python 3.12+
- Virtualenv activat (recomandat)
- Dependințe instalate (`pip install -r requirements.txt` dacă folosești un fișier de requirements)

## Pași de rulare

```bash
python manage.py migrate
python manage.py seed_hardware
python manage.py runserver
```

Necesită un superuser pentru zona de admin:

```bash
python manage.py createsuperuser
```

## Date demo

Comanda `python manage.py seed_hardware` și fișierul `hardware/fixtures/seed.json` adaugă:

- 3 categorii, 3 branduri, 3 materiale
- 5 produse cu restricțiile Laborator 3 (null, unique, choices, default, auto_now_add)
- Accesorii și 2 tutoriale video asociate

Comanda este idempotentă (poate fi rulată de mai multe ori).

## Rute publice

- `/` – Pagina principală
- `/catalog/` – Catalogul de produse (filtre după categorie/brand/preț și sortări)
- `/catalog/categorie/<slug>/` – Filtru după categorie
- `/catalog/brand/<slug>/` – Filtru după brand
- `/produs/<slug>/` – Detalii produs + accesorii și tutoriale asociate
- `/cart/` – Coș de cumpărături (cu rutele POST `/cart/add/<slug>/`, `/cart/update/<slug>/`, `/cart/remove/<slug>/`)
- `/contact/` – Formular de contact + confirmare
- `/tutoriale/` și `/tutoriale/<slug>/` – Listă tutoriale și detalii
- `/info/` – Detalii despre request curent
- `/log/` – Jurnalul accesărilor cu filtre și paginare
- `/blog/` – Listă articole demo (aplicația `core`, marcaj experimental)

Zona de administrare: `/admin/`.

## Trimitere email

În mediul de dezvoltare email-urile sunt redirecționate către consolă (setare `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"`). Testele folosesc backend-ul `locmem` pentru a verifica tranzacțiile.

## Teste

Rulează testele cu:

```bash
python manage.py test
```

Acoperă catalogul, coșul de cumpărături, jurnalizarea request-urilor și formularul de contact.
