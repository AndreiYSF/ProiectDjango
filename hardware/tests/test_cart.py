from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from hardware.models import Product


class CartTests(TestCase):
    fixtures = ["seed.json"]

    def test_add_to_cart_si_total_corect(self):
        product = Product.objects.get(slug="bormasina-percutie-bosch-gsb-13-re")
        add_url = reverse("hardware:cart_add", kwargs={"slug": product.slug})
        response = self.client.post(add_url, {"qty": 2})
        self.assertEqual(response.status_code, 302)

        session = self.client.session
        cart = session.get("cart", {})
        key = str(product.pk)
        self.assertIn(key, cart)
        self.assertEqual(cart[key]["qty"], 2)
        self.assertEqual(cart[key]["price"], str(product.price))

        cart_url = reverse("hardware:cart")
        response = self.client.get(cart_url)
        self.assertEqual(response.status_code, 200)
        expected_total = product.price * Decimal("2")
        self.assertEqual(response.context["total"], expected_total)

    def test_update_qty_si_remove(self):
        product = Product.objects.get(slug="surubelnita-electrica-dewalt-dcf601")
        self.client.post(
            reverse("hardware:cart_add", kwargs={"slug": product.slug}), {"qty": 1}
        )

        update_url = reverse("hardware:cart_update", kwargs={"slug": product.slug})
        response = self.client.post(update_url, {"qty": 5})
        self.assertEqual(response.status_code, 302)
        cart = self.client.session.get("cart", {})
        self.assertEqual(cart[str(product.pk)]["qty"], 5)

        remove_url = reverse("hardware:cart_remove", kwargs={"slug": product.slug})
        response = self.client.post(remove_url)
        self.assertEqual(response.status_code, 302)
        cart = self.client.session.get("cart", {})
        self.assertNotIn(str(product.pk), cart)
