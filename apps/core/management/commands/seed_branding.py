from django.core.management.base import BaseCommand
from apps.products.models import Category, Product
from django.utils.text import slugify
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seeds database with AETHEREAL branding data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding branding data...")
        
        # Categories
        cats_data = [
            ('Home Decor', 'home-decor'),
            ('Apparel & Accessories', 'apparel'),
            ('Wellness & Beauty', 'wellness'),
            ('Travel Essentials', 'travel')
        ]
        
        categories = {}
        for name, slug in cats_data:
            cat, created = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'description': f'Premium {name}'}
            )
            categories[slug] = cat
            if created:
                self.stdout.write(f"Created category: {name}")

        # Products (Matching Homepage Design)
        products_data = [
            {
                'name': 'The Artisan Table Lamp',
                'cat': 'home-decor',
                'price': '18500.00',
                'img': '/static/img/product1.jpg',
                'slug': 'artisan-table-lamp'
            },
            {
                'name': 'Silk Cashmere Throw',
                'cat': 'home-decor',
                'price': '24000.00',
                'img': '/static/img/product2.jpg',
                'slug': 'silk-cashmere-throw'
            },
            {
                'name': 'Premium Leather Weekender',
                'cat': 'travel',
                'price': '45000.00',
                'img': '/static/img/product3.jpg',
                'slug': 'leather-weekender'
            },
            {
                'name': 'Sculptural Vase Set',
                'cat': 'home-decor',
                'price': '9200.00',
                'img': '/static/img/product4.jpg',
                'slug': 'sculptural-vase-set'
            }
        ]

        for p_data in products_data:
            cat = categories[p_data['cat']]
            prod, created = Product.objects.get_or_create(
                slug=p_data['slug'],
                defaults={
                    'name': p_data['name'],
                    'admin_code': p_data['slug'].upper().replace('-', ''),
                    'category': cat,
                    'base_price': Decimal(p_data['price']),
                    'description': f"Experience the perfect blend of form and function with our {p_data['name']}.",
                    'image_urls': [p_data['img']],
                    'stock_quantity': 10
                }
            )
            if created:
                 self.stdout.write(f"Created product: {prod.name}")
            else:
                # Update image if needed (ensures demo images work)
                if not prod.image_urls:
                    prod.image_urls = [p_data['img']]
                    prod.save()
        
        self.stdout.write("Seeding Complete.")
