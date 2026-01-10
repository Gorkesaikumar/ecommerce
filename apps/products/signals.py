from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product, Category, DimensionConfig

@receiver([post_save, post_delete], sender=Product)
@receiver([post_save, post_delete], sender=Category)
@receiver([post_save, post_delete], sender=DimensionConfig)
def invalidate_product_cache(sender, instance, **kwargs):
    # Increment the cache version. 
    # All views using this version in their key will automatically fetch fresh data.
    try:
        cache.incr("product_cache_version")
    except ValueError:
        cache.set("product_cache_version", 1, timeout=None)
