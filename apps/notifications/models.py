"""
Notifications Models - Templates and Logs
"""
from django.db import models
import uuid

class NotificationTemplate(models.Model):
    """
    Templates for Email/SMS notifications.
    Supports variable substitution (e.g., {{ user_name }}).
    """
    TYPE_CHOICES = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification'),
    ]
    
    EVENT_CHOICES = [
        ('ORDER_CONFIRMED', 'Order Confirmed'),
        ('ORDER_SHIPPED', 'Order Shipped'),
        ('ORDER_DELIVERED', 'Order Delivered'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('WELCOME', 'Welcome Email'),
        ('OTP', 'OTP Verification'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    event = models.CharField(max_length=50, choices=EVENT_CHOICES)
    
    subject = models.CharField(max_length=255, blank=True, help_text="Subject for Emails")
    body = models.TextField(help_text="Content with {{ placeholders }}")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['type', 'event']

    def __str__(self):
        return f"{self.event} ({self.type})"


class NotificationLog(models.Model):
    """
    Log of sent notifications
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.CharField(max_length=255)
    type = models.CharField(max_length=10)
    event = models.CharField(max_length=50)
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('QUEUED', 'Queued'),
        ('RETRYING', 'Retrying')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True)
    
    # SMS-specific fields
    provider_response = models.JSONField(null=True, blank=True, help_text="MSG91 or other provider response")
    retry_count = models.IntegerField(default=0)
    
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.event} to {self.recipient} - {self.status}"
