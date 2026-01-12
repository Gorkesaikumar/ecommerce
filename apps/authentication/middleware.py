
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser
import logging

logger = logging.getLogger(__name__)

class JWTCookieMiddleware:
    """
    Middleware to populate request.user from 'access_token' cookie
    if the request is NOT for the Admin panel.
    
    This ensures Template Views (like Customer Dashboard) see the Customer user,
    even if an Admin Session exists (Isolation).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Admin Isolation: If accessing Admin Panel OR Admin API, skip JWT logic (Let Session rule)
        if request.path.startswith('/admin') or request.path.startswith('/api/v1/admin'):
            return self.get_response(request)

        # Optimization: If already authenticated by Session (and it's not Admin?), 
        # actually we want JWT to Override if present, to fix the specific bug.
        # But if Admin is logged in via Session, request.user is Admin.
        # If we are on `/account/dashboard`, we want Customer.
        
        # Check for JWT Cookie
        access_token = request.COOKIES.get('access_token')
        
        if access_token:
            try:
                # Use DRF's mechanism to validate (Reusing logic is safer)
                auth = JWTAuthentication()
                validated_token = auth.get_validated_token(access_token)
                user = auth.get_user(validated_token)
                
                if user:
                    request.user = user
                    request._cached_user = user
                    # logger.debug(f"Middleware: Authenticated Customer {user.mobile_number} via JWT Cookie")
            
            except Exception as e:
                # logger.warning(f"Middleware: JWT Cookie Validation Failed: {e}")
                pass
        
        return self.get_response(request)
