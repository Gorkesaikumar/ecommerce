"""
Location Verification APIs
"""
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from .models import ServiceArea, CustomerLocation, LocationAttempt
from .serializers import (
    VerifyLocationSerializer, ServiceAreaSerializer, 
    CustomerLocationSerializer, LocationAttemptSerializer,
    AdminServiceAreaSerializer
)
from .services import LocationService
from apps.core.models import AuditLog
import logging

logger = logging.getLogger('location')

# ====================== PUBLIC ENDPOINTS ======================

class VerifyLocationView(APIView):
    """
    POST /api/v1/location/verify
    Submit GPS coordinates for verification
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Rate limit: 5 requests per 10 minutes
        rate_limit_key = f"location:verify:{request.user.id}"
        attempts = cache.get(rate_limit_key, 0)
        
        if attempts >= 5:
            return Response({
                'error': 'Too many verification attempts. Please try again later.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Validate input
        serializer = VerifyLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        lat = data['latitude']
        long = data['longitude']
        accuracy = data['accuracy']
        
        try:
            # Basic coordinate validation
            LocationService.validate_coordinates(lat, long)
            
            # Reverse geocode
            geocoded = LocationService.reverse_geocode(lat, long)
            
            # Check service availability
            is_available, matched_area, denial_reason = LocationService.check_service_availability(geocoded)
            
            # Log attempt
            attempt = LocationAttempt.objects.create(
                user=request.user,
                latitude=lat,
                longitude=long,
                accuracy=accuracy,
                submitted_timestamp=data['timestamp'],
                city=geocoded.get('city', ''),
                district=geocoded.get('district', ''),
                state=geocoded.get('state', ''),
                country=geocoded.get('country', ''),
                was_allowed=is_available,
                denial_reason=denial_reason or '',
                matched_service_area=matched_area,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                correlation_id=getattr(request, 'correlation_id', None)
            )
            
            if is_available:
                # Update or create customer location
                with transaction.atomic():
                    location, created = CustomerLocation.objects.update_or_create(
                        user=request.user,
                        defaults={
                            'latitude': lat,
                            'longitude': long,
                            'accuracy': accuracy,
                            'city': geocoded['city'],
                            'district': geocoded.get('district', ''),
                            'state': geocoded['state'],
                            'country': geocoded['country'],
                            'full_address': geocoded.get('full_address', ''),
                            'is_verified': True,
                            'expires_at': timezone.now() + timedelta(hours=24),
                            'ip_address': self._get_client_ip(request),
                            'user_agent': request.META.get('HTTP_USER_AGENT', '')
                        }
                    )
                
                logger.info(f"Location verified for {request.user.mobile_number}: {geocoded['city']}, {geocoded['state']}")
                
                return Response({
                    'verified': True,
                    'location': {
                        'city': geocoded['city'],
                        'district': geocoded.get('district', ''),
                        'state': geocoded['state'],
                        'country': geocoded['country']
                    },
                    'expires_at': location.expires_at.isoformat(),
                    'message': f"Welcome! You are now verified in {geocoded['city']}"
                })
            
            else:
                # Denied
                logger.warning(f"Location denied for {request.user.mobile_number}: {denial_reason}")
                
                # Increment rate limit counter
                cache.set(rate_limit_key, attempts + 1, timeout=600)
                
                return Response({
                    'verified': False,
                    'reason': denial_reason,
                    'location_detected': {
                        'city': geocoded.get('city'),
                        'state': geocoded.get('state'),
                        'country': geocoded.get('country')
                    }
                }, status=status.HTTP_403_FORBIDDEN)
        
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Location verification error: {e}", exc_info=True)
            return Response({
                'error': 'Location verification failed. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class LocationStatusView(APIView):
    """
    GET /api/v1/location/status
    Check current location verification status
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            location = CustomerLocation.objects.get(user=request.user)
            serializer = CustomerLocationSerializer(location)
            return Response(serializer.data)
        
        except CustomerLocation.DoesNotExist:
            return Response({
                'is_verified': False,
                'message': 'Location not yet verified. Please allow location access.'
            })

class ServiceAreasPublicView(APIView):
    """
    GET /api/v1/location/service-areas
    Public endpoint to show available service areas
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        areas = ServiceArea.objects.filter(is_active=True)
        serializer = ServiceAreaSerializer(areas, many=True)
        
        return Response({
            'service_areas': serializer.data,
            'message': 'We currently serve the following areas'
        })

# ====================== ADMIN ENDPOINTS ======================

class AdminServiceAreaViewSet(viewsets.ModelViewSet):
    """
    Admin management of service areas
    """
    from apps.products.admin_views import IsAdminUser
    permission_classes = [IsAdminUser]
    queryset = ServiceArea.objects.all()
    serializer_class = AdminServiceAreaSerializer
    
    def perform_create(self, serializer):
        service_area = serializer.save(created_by=self.request.user)
        
        # Audit log
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='SERVICE_AREA_CREATED',
            resource_type='ServiceArea',
            resource_id=str(service_area.id),
            changes={'area': str(service_area)},
            reason='Service expansion',
            ip_address=self._get_client_ip(self.request),
            correlation_id=getattr(self.request, 'correlation_id', None)
        )
        
        logger.info(f"Service area created: {service_area}")
    
    def perform_update(self, serializer):
        service_area = serializer.save()
        
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='SERVICE_AREA_UPDATED',
            resource_type='ServiceArea',
            resource_id=str(service_area.id),
            changes={'area': str(service_area), 'is_active': service_area.is_active},
            reason='Service area modification',
            ip_address=self._get_client_ip(self.request),
            correlation_id=getattr(self.request, 'correlation_id', None)
        )
    
    def perform_destroy(self, instance):
        area_name = str(instance)
        
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='SERVICE_AREA_DELETED',
            resource_type='ServiceArea',
            resource_id=str(instance.id),
            changes={'area': area_name},
            reason='Service discontinuation',
            ip_address=self._get_client_ip(self.request),
            correlation_id=getattr(self.request, 'correlation_id', None)
        )
        
        instance.delete()
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class AdminLocationAttemptsView(APIView):
    """
    GET /api/v1/admin/location-attempts
    View all location verification attempts (with filters)
    """
    from apps.products.admin_views import IsAdminUser
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        queryset = LocationAttempt.objects.all().select_related('user')
        
        # Filter by allowed/denied
        was_allowed = request.query_params.get('was_allowed')
        if was_allowed is not None:
            queryset = queryset.filter(was_allowed=was_allowed.lower() == 'true')
        
        # Filter by date
        date_from = request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        
        # Limit to recent 100
        queryset = queryset[:100]
        
        serializer = LocationAttemptSerializer(queryset, many=True)
        return Response({
            'attempts': serializer.data,
            'total': queryset.count()
        })
