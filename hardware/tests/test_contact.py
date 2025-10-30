from pathlib import Path

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from hardware import views
from hardware.models import ContactMessage


class ContactViewTests(TestCase):
    fixtures = ["seed.json"]

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_contact_post_salveaza_message_si_afiseaza_confirmare(self):
        url = reverse("hardware:contact")
        messages_dir = Path(views.__file__).resolve().parent / "mesaje"
        existing = set(messages_dir.glob("mesaj_*.json"))

        payload = {
            "last_name": "Popescu",
            "first_name": "Ion",
            "birth_date": "1990-01-01",
            "email": "utilizator@example.com",
            "confirm_email": "utilizator@example.com",
            "message_type": "intrebare",
            "subject": "Intrebare disponibilitate",
            "min_wait_days": 3,
            "message": "Buna ziua, doresc informatii suplimentare despre stoc Popescu",
        }

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, url)

        self.assertTrue(
            ContactMessage.objects.filter(email=payload["email"]).exists()
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Popescu", mail.outbox[0].body)

        new_files = set(messages_dir.glob("mesaj_*.json")) - existing
        self.assertTrue(new_files)
