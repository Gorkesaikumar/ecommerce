"""
Admin Notification Views

Allows admins to send custom SMS notifications to customers.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.core.admin_views import IsAdminUser
from apps.notifications.services import NotificationService
import logging

logger = logging.getLogger(__name__)


class AdminSendNotificationView(APIView):
    """
    Admin endpoint to send SMS notifications to customers.
    
    POST /api/v1/admin/notifications/send/
    Payload: {
        "mobile_numbers": ["+919999999999", "+918888888888"],
        "message": "Your customization request has been approved!",
        "notification_type": "PROMOTIONAL"  # or "TRANSACTIONAL"
    }
    """
    permission_classes = [IsAdminUser]
    throttle_scope = 'admin_notifications'
    
    def post(self, request):
        mobile_numbers = request.data.get('mobile_numbers', [])
        message = request.data.get('message', '')
        notification_type = request.data.get('notification_type', 'CUSTOM')
        
        # Validation
        if not mobile_numbers or not isinstance(mobile_numbers, list):
            return Response(
                {"error": "mobile_numbers must be a non-empty list"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not message or len(message.strip()) == 0:
            return Response(
                {"error": "message is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # SMS length limit (160 chars for single SMS)
        if len(message) > 160:
            return Response(
                {"error": "Message exceeds 160 characters. Please shorten it."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Rate limit check (max 50 recipients per request)
        if len(mobile_numbers) > 50:
            return Response(
                {"error": "Cannot send to more than 50 recipients at once"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Send SMS to all recipients
        results = []
        for mobile in mobile_numbers:
            result = NotificationService.send_sms(
                mobile_number=mobile,
                message=message,
                event_type=f'ADMIN_{notification_type}'
            )
            results.append({
                'mobile': mobile,
                'success': result['success'],
                'message': result.get('message', '')
            })
        
        # Log admin action
        logger.info(
            f"Admin {request.user.email} sent notifications to {len(mobile_numbers)} recipients. "
            f"Type: {notification_type}"
        )
        
        # Create audit log
        from apps.core.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            user_mobile=request.user.mobile_number,
            user_role=request.user.role,
            action='ADMIN_NOTIFICATION_SENT',
            resource_type='Notification',
            changes={
                'recipient_count': len(mobile_numbers),
                'type': notification_type,
                'message_preview': message[:50]
            },
            reason='Admin notification broadcast',
            ip_address=self._get_client_ip(request)
        )
        
        success_count = sum(1 for r in results if r['success'])
        
        return Response({
            'message': f'Sent {success_count}/{len(mobile_numbers)} notifications successfully',
            'results': results
        }, status=status.HTTP_200_OK)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
