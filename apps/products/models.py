from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subcategories', on_delete=models.CASCADE)
    
    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    admin_code = models.CharField(max_length=50, unique=True, help_text="Internal SKU or Code")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base price in INR")
    description = models.TextField(blank=True)
    image_urls = models.JSONField(default=list, help_text="List of image URLs")
    
    # Inventory Management
    stock_quantity = models.PositiveIntegerField(default=0, help_text="Available stock")
    
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.admin_code} - {self.name}"

class DimensionConfig(models.Model):
    """
    Defines allowed dimension ranges and their pricing rules for a product.
    """
    product = models.ForeignKey(Product, related_name='dimension_configs', on_delete=models.CASCADE)
    
    min_length = models.FloatField(help_text="Min Length in cm")
    max_length = models.FloatField(help_text="Max Length in cm")
    
    min_breadth = models.FloatField(help_text="Min Breadth in cm")
    max_breadth = models.FloatField(help_text="Max Breadth in cm")
    
    min_height = models.FloatField(help_text="Min Height in cm") # Changed from min_breadth copy paste error checks
    max_height = models.FloatField(help_text="Max Height in cm")

    price_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, help_text="Multiplier for Base Price")
    price_add_on = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Flat add-on cost in INR")

    def __str__(self):
        return f"{self.product.name} Config ({self.min_length}-{self.max_length}L)"

class ProductDimension(models.Model):
    """
    Discrete dimension combination for a product with specific pricing.
    """
    product = models.ForeignKey(Product, related_name='dimensions', on_delete=models.CASCADE)
    length = models.FloatField(help_text="Length in cm")
    breadth = models.FloatField(help_text="Breadth in cm")
    height = models.FloatField(help_text="Height in cm")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price for this specific dimension")
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ('product', 'length', 'breadth', 'height')

    def __str__(self):
        return f"{self.product.name} ({self.length}x{self.breadth}x{self.height})"

class CustomizeRequest(models.Model):
    """
    Stores user requests for custom product dimensions.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('REVIEWED', 'Reviewed'),
        ('CONTACTED', 'Contacted'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]

    product = models.ForeignKey(Product, related_name='customize_requests', on_delete=models.CASCADE)
    user = models.ForeignKey('authentication.User', null=True, blank=True, on_delete=models.SET_NULL)
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    length = models.FloatField(help_text="Requested Length in cm")
    breadth = models.FloatField(help_text="Requested Breadth in cm")
    height = models.FloatField(help_text="Requested Height in cm")
    
    message = models.TextField(blank=True, help_text="Additional specific requirements")
    admin_note = models.TextField(blank=True, help_text="Admin's internal note or rejection reason")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Request by {self.name} for {self.product.name}"
