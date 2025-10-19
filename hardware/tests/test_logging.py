from django.test import TestCase
from django.urls import reverse

from hardware.models import RequestLog


class RequestLoggingTests(TestCase):
    fixtures = ["seed.json"]

    def test_request_logging_salveaza_in_db_pentru_rute_publice(self):
        self.assertEqual(RequestLog.objects.count(), 0)
        url = reverse("hardware:catalog")
        response = self.client.get(url, {"category": "scule-electrice"})
        self.assertEqual(response.status_code, 200)

        self.assertEqual(RequestLog.objects.count(), 1)
        log = RequestLog.objects.order_by("-created_at").first()
        self.assertEqual(log.path, url)
        self.assertEqual(log.method, "GET")
        self.assertIn("category=scule-electrice", log.querystring)
