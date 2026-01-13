"""
Order Lifecycle Signals

Automatically trigger SMS notifications when order status changes.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from .notification_templates import (
    get_order_placed_message,
    get_order_shipped_message,
    get_order_out_for_delivery_message,
    get_order_delivered_message
)
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def send_order_status_notification(sender, instance, created, **kwargs):
    """
    Send SMS notification when order status changes.
    
    IDEMPOTENCY: Uses database field `last_notified_status` to prevent duplicates.
    ASYNC: Uses Celery task for non-blocking SMS delivery.
    
    Triggers on:
    - Order creation (PENDING/PAID status)
    - Status change to SHIPPED, DELIVERED
    """
    current_status = instance.status
    
    # Check if we've already sent notification for this status
    if instance.last_notified_status == current_status:
        logger.debug(f"Order {instance.id}: Already notified for status {current_status}")
        return
    
    # Determine if we should send notification
    should_notify = False
    message = None
    event_type = None
    
    # Define which statuses trigger notifications
    notifiable_statuses = {
        'PENDING': ('ORDER_PLACED', get_order_placed_message),
        'PAID': ('ORDER_PLACED', get_order_placed_message),
        'SHIPPED': ('ORDER_SHIPPED', get_order_shipped_message),
        'OUT_FOR_DELIVERY': ('ORDER_OUT_FOR_DELIVERY', get_order_out_for_delivery_message),
        'DELIVERED': ('ORDER_DELIVERED', get_order_delivered_message),
    }
    
    if current_status in notifiable_statuses:
        should_notify = True
        event_type, message_func = notifiable_statuses[current_status]
        message = message_func(instance)
    
    # Send notification if needed
    if should_notify and message:
        mobile_number = instance.customer_mobile
        
        if not mobile_number:
            logger.warning(f"No mobile number for order {instance.id}")
            return
        
        # Send SMS asynchronously via Celery
        try:
            from apps.core.tasks import send_sms_async
            
            # Queue the SMS task (non-blocking)
            send_sms_async.delay(
                mobile_number=mobile_number,
                message=message,
                event_type=event_type
            )
            
            # Update last_notified_status to prevent duplicates
            # Use update() to avoid triggering signal again
            Order.objects.filter(pk=instance.pk).update(last_notified_status=current_status)
            
            logger.info(f"Order notification queued for {instance.id}: {event_type}")
            
        except Exception as e:
            logger.error(f"Error queuing order notification for {instance.id}: {e}")
            # Don't raise exception - order save should succeed even if notification fails
