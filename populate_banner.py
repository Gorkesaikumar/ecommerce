
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.promotions.models import MainBanner

# Create a sample banner
# Using a high quality Unsplash image for wood/interior
IMAGE_URL = "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?q=80&w=2000&auto=format&fit=crop"

if not MainBanner.objects.exists():
    MainBanner.objects.create(
        title="Timeless Comfort",
        subtitle="Discover our premium collection of handcrafted wooden furniture.",
        image_url=IMAGE_URL,
        cta_text="Shop Collection",
        redirect_url="/products/",
        priority=10,
        is_active=True
    )
    print("Created Sample Main Banner.")
else:
    print("Main Banner already exists.")
