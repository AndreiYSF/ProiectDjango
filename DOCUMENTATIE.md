# Django - proiect [Nume Prenume, Grupa]

## Pagina de titlu
- Numele site-ului: Magazin Hardware
- Nume student + grupa: [completati aici]

## Descriere proiect
Aplicația este un magazin hardware pentru scule și accesorii, cu catalog de produse, coș virtual, tutoriale video, formular de contact, jurnal de accesări și zonă de profil. Include funcționalități de autentificare, confirmare e-mail, feed promoțional și logging.

## Diagramă bază de date
- Diagrama: `hardware/docs/hardware_erd.drawio`

## Modele principale
- Product, Category, Brand, Material, Tutorial, Accessory
- User (custom, cu câmpuri suplimentare + confirmare e-mail + blocat)
- RequestLog, ContactMessage
- ProductView, Promotion
- Purchase, Nota, FeedbackRequest

## Laborator 5 – Formular produse
- Câmpuri extra: `base_price`, `markup_percentage` (preț final calculat).

## Laborator 8 – Securitate și permisiuni
- Confirmare e-mail, blocare login, grupuri admin/moderatori, pagini protejate.

## Laborator 9 – Scheduler & newsletter
- Taskuri periodice: ștergere utilizatori neconfirmați, newsletter, curățare loguri, curățare promoții.
- Conținut newsletter: recomandări de produse și tutoriale, cu text variat.

## Laborator 10 – Coș virtual + localStorage
- Stoc, cantități, +/-, input direct, badge “în coș”.
- Pagina localStorage cu sortare și totaluri.

## Laborator 11 – Cache / feedback / taguri
- Cache DB + caching pentru meniu, profil (5 zile), per_page produse.
- Feedback lunar pe email pentru achiziții, cu rating 1–5.
- SQL debug în `/log?sql=true`.
- Orar suport din fișier JSON.
- Produsul zilei în cache + tag.
- Tag preț EUR cu hover.
- Tag produse vizualizate azi (VIZ_PROD).

## Resurse
- Icon-uri: FontAwesome (CDN).
- Imagini: SVG-urile din `hardware/static/hardware/img/`.
