"""
Promotions Models - Promo codes, discounts, and usage tracking
"""
from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid
from django.utils import timezone

class PromoCode(models.Model):
    """
    Promotional codes (coupons)
    """
    DISCOUNT_TYPES = [
        ('PERCENT', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, help_text="Case insensitive code")
    description = models.TextField(blank=True)
    
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='PERCENT')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage value or Fixed Amount")
    
    max_discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Maximum discount cap for percentage based discounts"
    )
    
    min_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text="Minimum cart value required"
    )
    
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    usage_limit = models.IntegerField(null=True, blank=True, help_text="Total number of times this code can be used globally")
    usage_count = models.IntegerField(default=0)
    
    per_user_limit = models.IntegerField(default=1, help_text="How many times a single user can use this code")
    
    is_active = models.BooleanField(default=True)
    applicable_categories = models.ManyToManyField('products.Category', blank=True, help_text="If empty, applies to all")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'PERCENT' else ' Flat'}"

    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False, "Promo code is inactive"
        if now < self.valid_from:
            return False, f"Promo code starts on {self.valid_from.strftime('%Y-%m-%d %H:%M')}"
        if now > self.valid_until:
            return False, "Promo code is expired"
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False, "Promo code usage limit reached"
        return True, "Valid"

class PromoUsage(models.Model):
    """
    Tracks usage of promo codes by users/orders
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    promo = models.ForeignKey(PromoCode, on_delete=models.PROTECT, related_name='usages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='promo_usages')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-used_at']

# --- Marketing Content Models ---

class MarketingContent(models.Model):
    """Abstract base for marketing content"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Higher number = Higher priority")
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Soft Delete
    is_deleted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-priority', '-created_at']

class ScrollBanner(MarketingContent):
    """Marquee style scroll banner at top"""
    content = models.TextField(help_text="Text to display")
    background_color = models.CharField(max_length=20, default="#000000")
    text_color = models.CharField(max_length=20, default="#FFFFFF")
    link = models.CharField(max_length=500, blank=True, null=True, help_text="Local path or absolute URL")

    def __str__(self):
        return self.content[:50]

class MainBanner(MarketingContent):
    """Hero banner below header"""
    subtitle = models.CharField(max_length=200, blank=True)
    image_url = models.CharField(max_length=500, help_text="Image path or URL")
    cta_text = models.CharField(max_length=50, default="Shop Now")
    redirect_url = models.CharField(max_length=500, blank=True, help_text="Local path or absolute URL")

    def __str__(self):
        return self.title or "Main Banner"

class Promotion(MarketingContent):
    """Carousel items for promotions"""
    subtitle = models.CharField(max_length=200, blank=True)
    image_url = models.CharField(max_length=500, help_text="Image path or URL")
    redirect_url = models.CharField(max_length=500, blank=True)
    
    def __str__(self):
        return self.title or "Promotion"

class Popup(MarketingContent):
    """
    Admin-managed popups for the storefront
    """
    TYPE_CHOICES = [
        ('IMAGE', 'Image Only'),
        ('TEXT', 'Text Only'),
        ('IMAGE_LINK', 'Image + Link'),
        ('TEXT_CTA', 'Text + CTA'),
    ]
    DISPLAY_CHOICES = [
        ('ONCE_SESSION', 'Once per Session'),
        ('ONCE_USER', 'Once per User'),
        ('ALWAYS', 'Always'),
    ]

    popup_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='IMAGE')
    content = models.TextField(blank=True, help_text="Text content (HTML allowed for safe tags)")
    image = models.ImageField(upload_to='popups/', null=True, blank=True)
    redirect_url = models.CharField(max_length=500, blank=True, null=True, help_text="Link to redirect to")
    cta_text = models.CharField(max_length=50, blank=True, default="Learn More")
    
    display_rule = models.CharField(max_length=20, choices=DISPLAY_CHOICES, default='ONCE_SESSION')
    delay_seconds = models.IntegerField(default=0, help_text="Delay before showing (seconds)")

    def __str__(self):
        return self.title or f"Popup ({self.get_popup_type_display()})"
