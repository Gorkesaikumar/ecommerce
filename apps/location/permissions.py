"""
Location Enforcement Permission Class
"""
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.conf import settings
from apps.location.models import CustomerLocation
import logging

logger = logging.getLogger('location')

class HasVerifiedLocation(IsAuthenticated):
    """
    Permission class that requires:
    1. Authenticated user
    2. Valid location verification (not expired)
    
    Admins bypass this check for testing
    """
    message = "Location verification required. Please allow location access."
    
    def has_permission(self, request, view):
        # Explicit bypass for testing environments only
        # Must be explicitly set in settings - never auto-enabled
        if getattr(settings, 'SKIP_LOCATION_CHECK', False):
            return True
            
        # First check authentication
        if not super().has_permission(request, view):
            return False
        
        # Admin bypass
        if hasattr(request.user, 'role') and request.user.role == 'ADMIN':
            return True
        
        # Check location verification
        try:
            location = CustomerLocation.objects.get(user=request.user)
            
            # Check if expired
            if timezone.now() > location.expires_at:
                logger.warning(f"Expired location for {request.user.mobile_number}")
                self.message = "Location verification expired. Please verify your location again."
                return False
            
            # Check if verified
            if not location.is_verified:
                logger.warning(f"Unverified location for {request.user.mobile_number}")
                self.message = "Location not verified. Please complete location verification."
                return False
            
            return True
        
        except CustomerLocation.DoesNotExist:
            logger.warning(f"No location record for {request.user.mobile_number}")
            self.message = "Location verification required. Please allow location access to browse products."
            return False
