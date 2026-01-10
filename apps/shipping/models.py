"""
Shipping Models - Shipping zones, rates, and calculation
"""
from django.db import models
from decimal import Decimal
import uuid


class ShippingZone(models.Model):
    """
    Geographical zones for shipping rate calculation.
    Each zone can cover multiple states/regions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # States covered by this zone (JSON list)
    states = models.JSONField(
        default=list,
        help_text="List of state names covered by this zone"
    )
    
    # Zone priority (lower = checked first)
    priority = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({len(self.states)} states)"


class ShippingRate(models.Model):
    """
    Shipping rates for a zone based on order value and weight.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    zone = models.ForeignKey(
        ShippingZone, 
        on_delete=models.CASCADE,
        related_name='rates'
    )
    
    # Rate name for identification
    name = models.CharField(max_length=100)
    
    # Order value range
    min_order_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    max_order_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Leave blank for no upper limit"
    )
    
    # Base shipping rate
    base_rate = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Base shipping charge"
    )
    
    # Per-kg rate for weight-based shipping
    per_kg_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text="Additional charge per kg after base weight"
    )
    base_weight_kg = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('5.00'),
        help_text="Weight included in base rate"
    )
    
    # Free shipping threshold
    free_above = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Free shipping for orders above this amount"
    )
    
    # Estimated delivery days
    min_delivery_days = models.IntegerField(default=3)
    max_delivery_days = models.IntegerField(default=7)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['zone', 'min_order_value']
    
    def __str__(self):
        return f"{self.zone.name} - {self.name}: ₹{self.base_rate}"


class ShippingMethod(models.Model):
    """
    Available shipping methods (Standard, Express, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    
    # Rate multiplier (e.g., Express = 1.5x standard rate)
    rate_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal('1.00')
    )
    
    # Delivery time adjustment (negative = faster)
    delivery_days_adjustment = models.IntegerField(default=0)
    
    # Tracking availability
    has_tracking = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)  # Display order
    
    class Meta:
        ordering = ['priority']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class PincodeServiceability(models.Model):
    """
    Check if specific pincodes are serviceable.
    Used for delivery availability validation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pincode = models.CharField(max_length=10, unique=True)
    zone = models.ForeignKey(
        ShippingZone, 
        on_delete=models.CASCADE,
        related_name='pincodes'
    )
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    
    # COD availability
    cod_available = models.BooleanField(default=True)
    
    # Prepaid only areas
    prepaid_only = models.BooleanField(default=False)
    
    is_serviceable = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['pincode']
    
    def __str__(self):
        return f"{self.pincode} - {self.city}, {self.state}"
