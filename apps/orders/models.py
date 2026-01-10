from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid
from apps.products.models import Product

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='addresses', on_delete=models.CASCADE)
    line1 = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50, default='Telangana', editable=False)
    zip_code = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.state = 'Telangana'  # Enforce Business Rule
        super().save(*args, **kwargs)

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        AWAITING_PAYMENT = 'AWAITING_PAYMENT', 'Awaiting Payment'
        PAID = 'PAID', 'Paid'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    class PaymentMethod(models.TextChoices):
        ONLINE = 'ONLINE', 'Online Payment'
        COD = 'COD', 'Cash on Delivery'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.PROTECT, null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True, help_text="Email for guest orders")
    guest_phone = models.CharField(max_length=15, null=True, blank=True, help_text="Phone for guest orders")
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.ONLINE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.JSONField(help_text="Snapshot of address at time of order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.PROTECT)
    product_snapshot = models.JSONField(help_text="Snapshot of product name/code")
    
    # Selected Dimensions
    length = models.FloatField()
    breadth = models.FloatField()
    height = models.FloatField()
    
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='cart', on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    guest_email = models.EmailField(null=True, blank=True, help_text="Captured during guest checkout step")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Coupon / Promotion
    applied_promo = models.ForeignKey(
        'promotions.PromoCode', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='carts'
    )
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_cart', condition=models.Q(user__isnull=False)),
            models.UniqueConstraint(fields=['session_key'], name='unique_session_cart', condition=models.Q(session_key__isnull=False))
        ]

    def __str__(self):
        return f"Cart of {self.user.mobile_number if self.user else 'Guest ' + str(self.session_key)}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='cart_items', on_delete=models.CASCADE)
    
    # Store dimensions selected by user
    length = models.FloatField()
    breadth = models.FloatField()
    height = models.FloatField()
    
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ('cart', 'product', 'length', 'breadth', 'height')

    def __str__(self):
        return f"{self.product.name} ({self.length}x{self.breadth}x{self.height})"
