from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from hardware.models import ContactMessage


class ContactViewTests(TestCase):
    fixtures = ["seed.json"]

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_contact_post_salveaza_message_si_afiseaza_confirmare(self):
        url = reverse("hardware:contact")
        payload = {
            "name": "Utilizator Test",
            "email": "utilizator@example.com",
            "message": "Mesaj de test pentru formularul de contact.",
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, 201)
        self.assertTemplateUsed(response, "hardware/confirmation.html")
        self.assertTrue(
            ContactMessage.objects.filter(email=payload["email"]).exists()
        )
        self.assertIn("Mulțumim", response.content.decode("utf-8"))

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(payload["name"], mail.outbox[0].body)
