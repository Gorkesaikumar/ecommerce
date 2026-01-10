import logging
import json
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('audit')

class AuditLogMiddleware(MiddlewareMixin):
    """
    Logs critical write operations (POST, PUT, PATCH, DELETE) to a separate audit log.
    Focuses on Admin and sensitive User actions.
    """
    def process_response(self, request, response):
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            if response.status_code < 400: # Only log successful writes
                user = request.user if request.user.is_authenticated else 'Anonymous'
                path = request.path
                method = request.method
                
                # Identify User ID
                user_id = str(request.user.id) if request.user.is_authenticated else 'N/A'
                
                # In a real system, we might dump this to a DB table `audit_logs`
                # For now, we use a structured logger which can be shipped to ELK/CloudWatch
                log_data = {
                    'event': 'AUDIT_LOG',
                    'user_id': user_id,
                    'method': method,
                    'path': path,
                    'status': response.status_code,
                    'ip': self.get_client_ip(request)
                }
                
                logger.info(json.dumps(log_data))
        
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
