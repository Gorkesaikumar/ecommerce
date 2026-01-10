from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
from apps.orders.models import Order

class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        CAPTURED = 'CAPTURED', 'Captured'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, related_name='payment', on_delete=models.PROTECT)
    
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.TextField(blank=True, null=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.razorpay_order_id} - {self.status}"
