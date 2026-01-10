"""
Admin Login View - Email + Password Authentication
Separate from customer OTP authentication
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
import logging

from apps.authentication.models import User

logger = logging.getLogger(__name__)


class AdminLoginView(APIView):
    """
    Admin Login with Email + Password
    
    Only users with ADMIN role can authenticate via this endpoint.
    Returns JWT tokens on successful authentication.
    """
    permission_classes = [AllowAny]
    # Note: Rate limiting configured in settings.py REST_FRAMEWORK throttle classes
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Validate input
        if not email or not password:
            return Response(
                {'detail': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get user by email
            user = User.objects.filter(email=email).first()
            
            if not user:
                # Log failed attempt
                logger.warning(f'Admin login failed - Unknown email: {email}, IP: {self._get_client_ip(request)}')
                return Response(
                    {'detail': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Check if user is admin
            if user.role != User.Roles.ADMIN:
                # Log unauthorized access attempt
                logger.warning(f'Admin login unauthorized - Non-admin user: {email}, IP: {self._get_client_ip(request)}')
                return Response(
                    {'detail': 'Access denied. Admin credentials required.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Verify password
            if not user.check_password(password):
                # Log failed attempt
                logger.warning(f'Admin login failed - Invalid password for: {email}, IP: {self._get_client_ip(request)}')
                return Response(
                    {'detail': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Check if account is active
            if not user.is_active:
                return Response(
                    {'detail': 'Account is disabled'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Add custom claims
            refresh['role'] = user.role
            refresh['email'] = user.email

            # Establish Django Session (Crucial for HTML Admin Dashboard)
            from django.contrib.auth import login
            login(request, user)
            
            # Log successful login
            logger.info(f'Admin logged in successfully: {email}, IP: {self._get_client_ip(request)}')
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'name': user.name,
                    'role': user.role,
                    'mobile_number': user.mobile_number
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Admin login error: {str(e)}')
            return Response(
                {'detail': 'Authentication failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_client_ip(self, request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
