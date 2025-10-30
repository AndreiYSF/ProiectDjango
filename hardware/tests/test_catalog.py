from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from hardware.models import Brand, Category, Product


class CatalogViewTests(TestCase):
    fixtures = ["seed.json"]

    def test_catalog_list_status_code_si_paginare(self):
        url = reverse("hardware:catalog")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("products", response.context)
        self.assertLessEqual(len(response.context["products"]), 10)
        self.assertFalse(response.context["is_paginated"])

        category = Category.objects.get(slug="scule-electrice")
        brand = Brand.objects.get(slug="bosch")
        for index in range(15):
            Product.objects.create(
                category=category,
                brand=brand,
                name=f"Produs test {index}",
                slug=f"produs-test-{index}",
                description="Produs folosit pentru testarea paginării.",
                price=Decimal("99.99"),
                stock=5,
                available=True,
            )

        response = self.client.get(url)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(response.status_code, 200)

    def test_filters_category_brand_si_sort_price(self):
        category = Category.objects.get(slug="scule-electrice")
        brand = Brand.objects.get(slug="bosch")
        Product.objects.create(
            category=category,
            brand=brand,
            name="Produs ieftin",
            slug="produs-ieftin",
            price=Decimal("100.00"),
            stock=5,
            available=True,
        )
        Product.objects.create(
            category=category,
            brand=brand,
            name="Produs scump",
            slug="produs-scump",
            price=Decimal("900.00"),
            stock=5,
            available=True,
        )

        url = reverse("hardware:catalog")
        response = self.client.get(
            url,
            {
                "category": "scule-electrice",
                "brand": "bosch",
                "ord": "d",
            },
        )
        self.assertEqual(response.status_code, 200)
        products = list(response.context["products"])
        self.assertGreaterEqual(products[0].price, products[-1].price)

        brand_url = reverse("hardware:catalog_by_brand", kwargs={"slug": "dewalt"})
        response = self.client.get(brand_url)
        self.assertEqual(response.status_code, 200)
        for product in response.context["products"]:
            self.assertEqual(product.brand.slug, "dewalt")

    def test_product_detail_afiseaza_datele(self):
        product = Product.objects.get(slug="bormasina-percutie-bosch-gsb-13-re")
        url = reverse("hardware:product_detail", kwargs={"slug": product.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.name)
        price_display = str(product.price).replace(".", ",")
        self.assertContains(response, price_display)
