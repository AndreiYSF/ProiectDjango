from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from hardware.models import (
    Accessory,
    Brand,
    Category,
    Material,
    Product,
    Tutorial,
)


class Command(BaseCommand):
    help = "Populează baza de date cu date demonstrative pentru aplicația hardware."

    def handle(self, *args, **options):
        categories = self._create_categories()
        brands = self._create_brands()
        materials = self._create_materials()
        products = self._create_products(categories, brands, materials)
        self._create_accessories(products)
        self._create_tutorials(products)
        self.stdout.write(self.style.SUCCESS("Seed hardware finalizat."))

    def _create_categories(self) -> dict[str, Category]:
        data = [
            {
                "slug": "scule-electrice",
                "name": "Scule electrice",
                "description": "Scule electrice pentru lucru intens: bormașini, șurubelnițe, polizoare.",
            },
            {
                "slug": "scule-manuale",
                "name": "Scule manuale",
                "description": "Unelte de bază pentru atelier: truse, clești, chei și accesorii manuale.",
            },
            {
                "slug": "echipamente-protectie",
                "name": "Echipamente de protecție",
                "description": "Îmbrăcăminte și accesorii pentru siguranță în timpul lucrului.",
            },
        ]
        categories: dict[str, Category] = {}
        for item in data:
            category, created = Category.objects.get_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "description": item["description"],
                },
            )
            if not created:
                category.name = item["name"]
                category.description = item["description"]
                category.save(update_fields=["name", "description"])
            categories[item["slug"]] = category
        return categories

    def _create_brands(self) -> dict[str, Brand]:
        data = [
            {
                "slug": "bosch",
                "name": "Bosch",
                "country": "Germania",
                "founded_year": 1886,
            },
            {
                "slug": "dewalt",
                "name": "DeWalt",
                "country": "Statele Unite",
                "founded_year": 1924,
            },
            {
                "slug": "makita",
                "name": "Makita",
                "country": "Japonia",
                "founded_year": 1915,
            },
        ]
        brands: dict[str, Brand] = {}
        for item in data:
            brand, created = Brand.objects.get_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "country": item["country"],
                    "founded_year": item["founded_year"],
                },
            )
            if not created:
                brand.name = item["name"]
                brand.country = item["country"]
                brand.founded_year = item["founded_year"]
                brand.save(update_fields=["name", "country", "founded_year"])
            brands[item["slug"]] = brand
        return brands

    def _create_materials(self) -> dict[str, Material]:
        data = [
            {
                "slug": "otel-carbon",
                "name": "Oțel carbon",
                "description": "Alloy rezistent folosit la scule profesionale.",
                "recyclable": True,
            },
            {
                "slug": "plastic-abs",
                "name": "Plastic ABS",
                "description": "Plastic rezistent la impact folosit pentru carcase.",
                "recyclable": False,
            },
            {
                "slug": "aluminiu",
                "name": "Aluminiu",
                "description": "Material ușor, ideal pentru accesorii portabile.",
                "recyclable": True,
            },
        ]

        materials: dict[str, Material] = {}
        for item in data:
            material, created = Material.objects.get_or_create(
                name=item["name"],
                defaults={
                    "description": item["description"],
                    "recyclable": item["recyclable"],
                },
            )
            if not created:
                material.description = item["description"]
                material.recyclable = item["recyclable"]
                material.save(update_fields=["description", "recyclable"])
            materials[item["slug"]] = material
        return materials

    def _create_products(
        self,
        categories: dict[str, Category],
        brands: dict[str, Brand],
        materials: dict[str, Material],
    ) -> dict[str, Product]:
        data = [
            {
                "slug": "bormasina-percutie-bosch-gsb-13-re",
                "name": "Bormașină cu percuție Bosch GSB 13 RE",
                "category": "scule-electrice",
                "brand": "bosch",
                "description": "Bormașină compactă cu percuție, 600 W, ideală pentru utilizare zilnică.",
                "price": Decimal("439.90"),
                "stock": 24,
                "available": True,
                "condition": Product.Condition.NEW,
                "materials": ["otel-carbon", "plastic-abs"],
            },
            {
                "slug": "surubelnita-electrica-dewalt-dcf601",
                "name": "Șurubelniță electrică DeWalt DCF601",
                "category": "scule-electrice",
                "brand": "dewalt",
                "description": "Șurubelniță cu acumulator, 12V XR, ideală pentru montaj rapid.",
                "price": Decimal("629.00"),
                "stock": 15,
                "available": True,
                "condition": Product.Condition.NEW,
                "materials": ["plastic-abs"],
            },
            {
                "slug": "trusa-scule-108-piese-makita",
                "name": "Trusă scule 108 piese Makita",
                "category": "scule-manuale",
                "brand": "makita",
                "description": "Trusă completă pentru atelier, conține chei tubulare, biți și adaptori.",
                "price": Decimal("389.50"),
                "stock": 40,
                "available": True,
                "condition": Product.Condition.NEW,
                "materials": ["otel-carbon"],
            },
            {
                "slug": "polizor-unghiular-bosch-gws-750",
                "name": "Polizor unghiular Bosch GWS 750",
                "category": "scule-electrice",
                "brand": "bosch",
                "description": "Polizor unghiular 750 W, disc 115 mm, pentru lucru intens.",
                "price": Decimal("349.00"),
                "stock": 10,
                "available": True,
                "condition": Product.Condition.REFURBISHED,
                "materials": ["otel-carbon", "plastic-abs"],
            },
            {
                "slug": "casti-antifonice-makita-padded",
                "name": "Căști antifonice Makita Padded",
                "category": "echipamente-protectie",
                "brand": "makita",
                "description": None,
                "price": Decimal("119.90"),
                "stock": 35,
                "available": True,
                "condition": Product.Condition.USED,
                "materials": ["plastic-abs", "aluminiu"],
            },
        ]

        products: dict[str, Product] = {}
        for item in data:
            category = categories[item["category"]]
            brand = brands[item["brand"]]
            defaults = {
                "name": item["name"],
                "category": category,
                "brand": brand,
                "description": item["description"],
                "price": item["price"],
                "stock": item["stock"],
                "available": item["available"],
                "condition": item["condition"],
            }

            product, _ = Product.objects.update_or_create(
                slug=item["slug"],
                defaults=defaults,
            )
            product.materials.set(
                [materials[slug] for slug in item.get("materials", [])]
            )
            products[item["slug"]] = product
        return products

    def _create_accessories(self, products: dict[str, Product]) -> None:
        data = [
            {
                "product": "bormasina-percutie-bosch-gsb-13-re",
                "name": "Set burghie beton Bosch 5 piese",
                "compatibility_notes": "Compatibil cu mandrina de 13 mm.",
                "price": Decimal("59.90"),
                "requires_professional_installation": False,
            },
            {
                "product": "polizor-unghiular-bosch-gws-750",
                "name": "Set discuri tăiere metal 125 mm",
                "compatibility_notes": "Se recomandă respectarea vitezei maxime de rotație.",
                "price": Decimal("49.50"),
                "requires_professional_installation": False,
            },
        ]
        for item in data:
            product = products[item["product"]]
            Accessory.objects.update_or_create(
                product=product,
                name=item["name"],
                defaults={
                    "compatibility_notes": item["compatibility_notes"],
                    "price": item["price"],
                    "requires_professional_installation": item[
                        "requires_professional_installation"
                    ],
                },
            )

    def _create_tutorials(self, products: dict[str, Product]) -> None:
        tz = timezone.get_current_timezone()
        data = [
            {
                "slug": "ghid-bormasina-percutie",
                "title": "Cum folosești corect o bormașină cu percuție",
                "video_url": "https://www.example.com/video/bormasina-percutie",
                "description": "Tehnici de găurire în zidărie și beton pentru rezultate profesionale.",
                "duration_minutes": 18,
                "difficulty": "Intermediar",
                "published_at": timezone.make_aware(
                    datetime(2024, 3, 21, 10, 0), tz
                ),
                "products": [
                    "bormasina-percutie-bosch-gsb-13-re",
                    "surubelnita-electrica-dewalt-dcf601",
                ],
            },
            {
                "slug": "sfaturi-polizor-unghiular",
                "title": "Sfaturi de siguranță pentru polizorul unghiular",
                "video_url": "https://www.example.com/video/polizor-unghiular",
                "description": "Protecție, discuri potrivite și tehnici pentru tăieturi curate.",
                "duration_minutes": 12,
                "difficulty": "Începător",
                "published_at": timezone.make_aware(
                    datetime(2024, 2, 10, 9, 30), tz
                ),
                "products": [
                    "polizor-unghiular-bosch-gws-750",
                ],
            },
        ]

        for item in data:
            tutorial, _ = Tutorial.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "title": item["title"],
                    "video_url": item["video_url"],
                    "description": item["description"],
                    "duration_minutes": item["duration_minutes"],
                    "difficulty": item["difficulty"],
                    "published_at": item["published_at"],
                },
            )
            product_instances = [
                products[slug]
                for slug in item.get("products", [])
                if slug in products
            ]
            tutorial.products.set(product_instances)
