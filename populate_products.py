
import os
import django
import random
import requests
from django.core.files.base import ContentFile
from decimal import Decimal

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.products.models import Product, Category, ProductImage, ProductDimension, DimensionConfig

# Data Definition
PRODUCTS_DATA = [
    {
        "name": "Premium Teak Chopping Board",
        "category": "Kitchen Items",
        "price": 1200,
        "description": "Crafted from a single piece of premium teak wood, this chopping board offers durability and natural anti-bacterial properties. Its smooth finish and robust grain make it a perfect addition to any modern kitchen. Treat it with oil periodically to maintain its luster.",
        "dimensions": [(30, 20, 2, 1200), (40, 30, 2.5, 1500)],
        "keywords": "cutting board,wood,kitchen"
    },
    {
        "name": "Hand-Carved Wooden Spoons (Set of 3)",
        "category": "Kitchen Items",
        "price": 450,
        "description": "A set of three distinctively hand-carved wooden spoons, essential for mixing, serving, and cooking. Made from neem wood, they are gentle on non-stick cookware and heat resistant.",
        "dimensions": [(25, 5, 1, 450)],
        "keywords": "wooden spoon,kitchen,utensil"
    },
    {
        "name": "Rustic Spice Rack",
        "category": "Kitchen Items",
        "price": 950,
        "description": "Organize your spices with this rustic 2-tier wooden rack. Designed to sit on your countertop or be mounted on the wall, it adds a farmhouse charm to your cooking space.",
        "dimensions": [(30, 10, 15, 950)],
        "keywords": "spice rack,wood shelf,kitchen"
    },
    {
        "name": "Floating Hexagon Shelf",
        "category": "Wall shelf and hanging",
        "price": 800,
        "description": "Add a geometric touch to your walls with this honeycomb-shaped floating shelf. Perfect for displaying small succulents, photos, or collectibles. Easy to mount with hidden brackets.",
        "dimensions": [(25, 10, 25, 800), (30, 12, 30, 1100)],
        "keywords": "hexagon shelf,wood,wall decor"
    },
    {
        "name": "Corner Zig-Zag Shelf",
        "category": "Wall shelf and hanging",
        "price": 1100,
        "description": "Maximize your space with this clever 5-tier corner shelf. Its zig-zag design fits perfectly into any 90-degree corner, turning dead space into a stylish display area.",
        "dimensions": [(20, 20, 120, 1100)],
        "keywords": "corner shelf,wood,furniture"
    },
    {
        "name": "Wooden Elephant Figurine",
        "category": "Hand craft wooden",
        "price": 650,
        "description": "A symbol of wisdom and luck, this hand-carved wooden elephant showcases intricate detailing. Made by skilled artisans, it makes for a thoughtful gift or a charming decor piece.",
        "dimensions": [(12, 6, 10, 650)],
        "keywords": "elephant carving,wood art,statue"
    },
    {
        "name": "Antique Finish Jewelry Box",
        "category": "Hand craft wooden",
        "price": 1400,
        "description": "Keep your treasures safe in this vintage-style wooden jewelry box. Features brass inlays, velvet lining, and a secure latch. A timeless piece for your dressing table.",
        "dimensions": [(15, 10, 8, 1400)],
        "keywords": "jewelry box,wood box,antique"
    },
    {
        "name": "Geometric Wooden Pendant Lamp",
        "category": "Hanging wall Light",
        "price": 1350,
        "description": "Illuminate your room with this modern Scandinavian-inspired pendant light. The wooden slats create a warm, diffused glow and beautiful shadow patterns on your walls.",
        "dimensions": [(25, 25, 30, 1350)],
        "keywords": "wooden lamp,light fixture,pendant"
    },
    {
        "name": "Carved Mandala Wall Art",
        "category": "Hall walls accessories",
        "price": 1500,
        "description": "Transform your living room wall with this stunning laser-cut wooden mandala. The intricate floral patterns bring a sense of peace and artistic elegance to any space.",
        "dimensions": [(60, 2, 60, 1500)],
        "keywords": "mandala wall art,wood decor,carving"
    },
    {
        "name": "Hook Rail Key Holder",
        "category": "Hall walls accessories",
        "price": 350,
        "description": "Never lose your keys again with this minimalist wooden key holder. Features 5 strong hooks and a small shelf for mail or sunglasses. Mounts easily near your entryway.",
        "dimensions": [(30, 5, 8, 350)],
        "keywords": "key holder,wood hook,entryway"
    }
]

def download_image(keywords, index):
    """
    Downloads a random image from LoremFlickr based on keywords.
    """
    try:
        # Use random size slightly to avoid caching identical images if calling rapidly
        width = 800
        height = 800
        url = f"https://loremflickr.com/{width}/{height}/{keywords.replace(' ', ',')}/all?lock={random.randint(1,1000)}"
        print(f"  Downloading image from {url}...")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return ContentFile(response.content, name=f"product_{index}.jpg")
    except Exception as e:
        print(f"  Failed to download image: {e}")
    return None

def create_products():
    print("="*50)
    print("STARTING PRODUCT GENERATION")
    print("="*50)

    created_count = 0

    for idx, data in enumerate(PRODUCTS_DATA):
        # 1. Get Category
        try:
            category = Category.objects.get(name__iexact=data['category'])
        except Category.DoesNotExist:
            print(f"Skipping {data['name']}: Category '{data['category']}' not found.")
            continue

        # 2. Create Product
        product, created = Product.objects.get_or_create(
            name=data['name'],
            defaults={
                "category": category,
                "admin_code": f"SKU-{random.randint(10000, 99999)}",
                "base_price": data['price'],
                "description": data['description'],
                "stock_quantity": random.randint(10, 100),
            }
        )
        
        if not created:
            print(f"Updated existing product: {product.name}")
        else:
            print(f"Created new product: {product.name}")

        # 3. Create Dimensions
        for l, b, h, price in data['dimensions']:
            ProductDimension.objects.get_or_create(
                product=product,
                length=l,
                breadth=b,
                height=h,
                defaults={"price": price, "is_default": True}
            )

        # 4. Create Images (3 per product)
        current_images = product.images.count()
        if current_images < 3:
            needed = 3 - current_images
            print(f"  Adding {needed} images...")
            for i in range(needed):
                image_file = download_image(data['keywords'], i)
                if image_file:
                    ProductImage.objects.create(
                        product=product,
                        image=image_file,
                        alt_text=f"{product.name} View {i+1}",
                        is_feature=(i==0 and current_images==0),
                        order=i
                    )
        else:
            print("  Images already exist.")
        
        created_count += 1

    print("="*50)
    print(f"COMPLETED. Processed {created_count} products.")
    print("="*50)

if __name__ == "__main__":
    create_products()
