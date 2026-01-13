
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.products.models import Category

print("-" * 30)
print("EXISTING CATEGORIES")
print("-" * 30)
for cat in Category.objects.all():
    print(f"ID: {cat.id} | Name: {cat.name} | Slug: {cat.slug} | Parent: {cat.parent}")
print("-" * 30)
