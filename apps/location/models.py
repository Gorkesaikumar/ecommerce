from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class ServiceArea(models.Model):
    """
    Admin-configurable service areas.
    Hierarchical: Country > State > District > City
    Empty field = entire parent level (e.g., empty city = entire district)
    """
    country = models.CharField(max_length=100, default='India')
    state = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Optional bounding box for precision
    lat_min = models.FloatField(null=True, blank=True, help_text="Southern boundary")
    lat_max = models.FloatField(null=True, blank=True, help_text="Northern boundary")
    long_min = models.FloatField(null=True, blank=True, help_text="Western boundary")
    long_max = models.FloatField(null=True, blank=True, help_text="Eastern boundary")
    
    # Control
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='created_service_areas'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['country', 'state', 'district', 'city']]
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['state', 'district', 'city'])
        ]
        ordering = ['country', 'state', 'district', 'city']
    
    def __str__(self):
        parts = [p for p in [self.city, self.district, self.state, self.country] if p]
        return ', '.join(parts) if parts else 'Global'
    
    def matches_location(self, geocoded_data):
        """
        Check if geocoded location matches this service area.
        Empty fields match any value (hierarchical matching)
        """
        # Check country (required)
        if self.country and geocoded_data.get('country', '').lower() != self.country.lower():
            return False
        
        # Check state (if specified)
        if self.state and geocoded_data.get('state', '').lower() != self.state.lower():
            return False
        
        # Check district (if specified)
        if self.district and geocoded_data.get('district', '').lower() != self.district.lower():
            return False
        
        # Check city (if specified)
        if self.city and geocoded_data.get('city', '').lower() != self.city.lower():
            return False
        
        return True

class CustomerLocation(models.Model):
    """
    Tracks customer's last verified location with TTL
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='current_location'
    )
    
    # Submitted coordinates
    latitude = models.FloatField()
    longitude = models.FloatField()
    accuracy = models.FloatField(help_text="GPS accuracy in meters")
    
    # Reverse-geocoded data (server-side, trusted)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    full_address = models.TextField(blank=True)
    
    # Verification status
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    # Metadata
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['is_verified', 'expires_at']),
            models.Index(fields=['user', 'is_verified'])
        ]
    
    def __str__(self):
        return f"{self.user.mobile_number} - {self.city}, {self.state}"
    
    def is_valid(self):
        """Check if location is still valid (not expired)"""
        return self.is_verified and timezone.now() <= self.expires_at
    
    def time_until_expiry(self):
        """Get remaining time before expiry"""
        if not self.is_verified:
            return timedelta(0)
        remaining = self.expires_at - timezone.now()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)

class LocationAttempt(models.Model):
    """
    Audit log of all location verification attempts
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='location_attempts'
    )
    
    # Submitted data
    latitude = models.FloatField()
    longitude = models.FloatField()
    accuracy = models.FloatField()
    submitted_timestamp = models.DateTimeField()
    
    # Geocoded result
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Outcome
    was_allowed = models.BooleanField()
    denial_reason = models.CharField(max_length=500, blank=True)
    matched_service_area = models.ForeignKey(
        ServiceArea, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    correlation_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['was_allowed', 'timestamp']),
            models.Index(fields=['-timestamp'])
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        status = "ALLOWED" if self.was_allowed else "DENIED"
        return f"{self.user.mobile_number} - {status} - {self.timestamp}"
