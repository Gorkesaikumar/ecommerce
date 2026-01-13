
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.products.models import Product

print("-" * 50)
print("PRODUCT VERIFICATION")
print("-" * 50)
products = Product.objects.all()
print(f"Total Products: {products.count()}")
print("-" * 50)

for p in products:
    img_count = p.images.count()
    dim_count = p.dimensions.count()
    print(f"Product: {p.name[:30]}... | Price: {p.base_price} | Images: {img_count} | Dims: {dim_count}")
    if img_count < 3:
        print("  WARNING: Fewer than 3 images!")

print("-" * 50)
