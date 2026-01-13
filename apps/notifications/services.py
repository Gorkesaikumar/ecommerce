"""
Notifications Service
Handles sending of emails and SMS
"""
from django.core.mail import send_mail
from django.conf import settings
from .models import NotificationTemplate, NotificationLog
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    
    @staticmethod
    def send_notification(event_type: str, recipient: str, context: dict, channels=['EMAIL']):
        """
        Send notification for an event.
        channels: list of 'EMAIL', 'SMS'
        """
        if 'EMAIL' in channels:
            NotificationService._send_email(event_type, recipient, context)
            
        # SMS implementation would go here (e.g. Twilio/SNS)
        if 'SMS' in channels:
             logger.info(f"SMS would be sent to {recipient} for {event_type}")

    @staticmethod
    def _send_email(event_type: str, recipient_email: str, context: dict):
        try:
            template = NotificationTemplate.objects.get(type='EMAIL', event=event_type, is_active=True)
        except NotificationTemplate.DoesNotExist:
            logger.warning(f"No active email template for event: {event_type}")
            return

        try:
            # Simple variable substitution
            subject = template.subject
            body = template.body
            for key, value in context.items():
                placeholder = f"{{{{ {key} }}}}"
                body = body.replace(placeholder, str(value))
                subject = subject.replace(placeholder, str(value))
            
            # Send (Mock or Real)
            if settings.DEBUG:
                logger.info(f"--- EMAIL TO {recipient_email} ---\nSubject: {subject}\nBody:\n{body}\n----------------")
                status = 'SENT'
                error = ''
            else:
                logger.info(f"Prod Email Queue: {recipient_email} - {subject}")
                status = 'SENT'
                error = ''

        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {e}")
            status = 'FAILED'
            error = str(e)
            
        # Log it
        NotificationLog.objects.create(
            recipient=recipient_email,
            type='EMAIL',
            event=event_type,
            status=status,
            error_message=error,
            content=f"Subject: {subject}\n\n{body}"
        )
    
    @staticmethod
    def send_sms(mobile_number: str, message: str, event_type: str = 'CUSTOM') -> dict:
        """
        Send SMS notification.
        
        Args:
            mobile_number: Recipient mobile (with country code)
            message: SMS content
            event_type: Event type for logging
            
        Returns:
            dict with success status
        """
        try:
            from apps.core.services.msg91_provider import get_sms_service
            sms_service = get_sms_service()
            
            # Send via MSG91
            result = sms_service.send_transactional(mobile_number, message)
            
            # Log the notification
            NotificationLog.objects.create(
                recipient=mobile_number,
                type='SMS',
                event=event_type,
                status='SENT' if result['success'] else 'FAILED',
                error_message=result.get('message', ''),
                provider_response=result.get('provider_response', {}),
                content=message
            )
            
            return result
            
        except Exception as e:
            logger.error(f"SMS service error for {mobile_number}: {e}")
            
            # Log failure
            NotificationLog.objects.create(
                recipient=mobile_number,
                type='SMS',
                event=event_type,
                status='FAILED',
                error_message=str(e),
                content=message
            )
            
            return {'success': False, 'message': str(e)}
