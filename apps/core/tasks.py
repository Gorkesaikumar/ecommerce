"""
Celery Tasks for Asynchronous SMS Notifications

These tasks handle SMS delivery in the background, preventing blocking operations.
"""
from celery import shared_task
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_sms_async(self, mobile_number, message, event_type='CUSTOM'):
    """
    Send SMS asynchronously with automatic retry.
    
    Args:
        mobile_number: Recipient mobile number
        message: SMS content
        event_type: Event type for logging
        
    Retry strategy:
        - Max 3 retries
        - Exponential backoff: 30s, 60s, 120s
    """
    try:
        from apps.notifications.services import NotificationService
        
        result = NotificationService.send_sms(
            mobile_number=mobile_number,
            message=message,
            event_type=event_type
        )
        
        if not result['success']:
            # Retry on failure (network issues, provider downtime)
            raise self.retry(
                exc=Exception(f"SMS delivery failed: {result.get('message')}"),
                countdown=30 * (2 ** self.request.retries)  # Exponential backoff
            )
        
        return result
        
    except Exception as e:
        logger.error(f"SMS task error for {mobile_number}: {e}")
        
        # Retry if we haven't hit max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=30 * (2 ** self.request.retries))
        else:
            # Max retries reached, log and give up
            logger.critical(f"SMS delivery failed after {self.max_retries} retries: {mobile_number}")
            return {'success': False, 'message': str(e)}


@shared_task(bind=True, max_retries=3)
def send_otp_sms_async(self, mobile_number, otp):
    """
    Send OTP SMS asynchronously.
    
    Args:
        mobile_number: Recipient mobile number
        otp: OTP code
        
    Note: OTP SMS has higher priority, shorter retry delay
    """
    try:
        from apps.core.services.msg91_provider import get_sms_service
        
        sms_service = get_sms_service()
        result = sms_service.send_otp(mobile_number, otp)
        
        if not result['success']:
            # Retry with shorter countdown for OTP (time-sensitive)
            raise self.retry(
                exc=Exception(f"OTP SMS failed: {result.get('message')}"),
                countdown=10  # Only 10s delay for OTP retries
            )
        
        return result
        
    except Exception as e:
        logger.error(f"OTP SMS task error for {mobile_number}: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=10)
        else:
            logger.critical(f"OTP SMS failed after retries: {mobile_number}")
            return {'success': False, 'message': str(e)}


@shared_task
def send_order_notification_async(order_id, message, event_type):
    """
    Send order notification SMS asynchronously.
    
    Args:
        order_id: UUID of the order
        message: SMS content
        event_type: Notification event type
    """
    try:
        from apps.orders.models import Order
        
        order = Order.objects.get(pk=order_id)
        mobile_number = order.customer_mobile
        
        if not mobile_number:
            logger.warning(f"No mobile number for order {order_id}")
            return {'success': False, 'message': 'No mobile number'}
        
        # Use the generic send_sms_async task with retry logic
        return send_sms_async.delay(mobile_number, message, event_type)
        
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for SMS notification")
        return {'success': False, 'message': 'Order not found'}
    except Exception as e:
        logger.error(f"Order notification task error: {e}")
        return {'success': False, 'message': str(e)}
