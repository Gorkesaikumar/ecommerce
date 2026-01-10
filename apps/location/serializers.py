from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta
from .models import ServiceArea, CustomerLocation, LocationAttempt

class VerifyLocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    accuracy = serializers.FloatField(min_value=0, help_text="GPS accuracy in meters")
    timestamp = serializers.DateTimeField()
    
    def validate_timestamp(self, value):
        """Ensure timestamp is recent (within 5 minutes)"""
        now = timezone.now()
        age = abs((now - value).total_seconds())
        
        if age > 300:  # 5 minutes
            raise serializers.ValidationError("Location data is stale. Please retry.")
        
        return value
    
    def validate_accuracy(self, value):
        """Reject low-accuracy GPS data"""
        MAX_ACCURACY = 100  # meters
        
        if value > MAX_ACCURACY:
            raise serializers.ValidationError(
                f"GPS accuracy too low ({value}m). Please ensure good GPS signal."
            )
        
        return value

class ServiceAreaSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceArea
        fields = ['id', 'country', 'state', 'district', 'city', 
                  'is_active', 'display_name', 'created_at']
        read_only_fields = ['created_at']
    
    def get_display_name(self, obj):
        return str(obj)

class AdminServiceAreaSerializer(serializers.ModelSerializer):
    created_by_mobile = serializers.CharField(source='created_by.mobile_number', read_only=True)
    
    class Meta:
        model = ServiceArea
        fields = ['id', 'country', 'state', 'district', 'city',
                  'lat_min', 'lat_max', 'long_min', 'long_max',
                  'is_active', 'created_by', 'created_by_mobile', 
                  'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Ensure at least country is specified"""
        if not data.get('country'):
            raise serializers.ValidationError("Country is required")
        
        # Validate bounding box if provided
        if any([data.get('lat_min'), data.get('lat_max'), 
                data.get('long_min'), data.get('long_max')]):
            if not all([data.get('lat_min'), data.get('lat_max'), 
                       data.get('long_min'), data.get('long_max')]):
                raise serializers.ValidationError(
                    "All bounding box coordinates required if any is provided"
                )
        
        return data

class LocationAttemptSerializer(serializers.ModelSerializer):
    user_mobile = serializers.CharField(source='user.mobile_number', read_only=True)
    
    class Meta:
        model = LocationAttempt
        fields = ['id', 'user_mobile', 'latitude', 'longitude', 'accuracy',
                  'city', 'district', 'state', 'country', 
                  'was_allowed', 'denial_reason', 'timestamp', 'ip_address']

class CustomerLocationSerializer(serializers.ModelSerializer):
    time_remaining = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerLocation
        fields = ['city', 'district', 'state', 'country', 
                  'is_verified', 'verified_at', 'expires_at',
                  'time_remaining', 'is_valid']
    
    def get_time_remaining(self, obj):
        """Human-readable time until expiry"""
        remaining = obj.time_until_expiry()
        if remaining.total_seconds() <= 0:
            return "Expired"
        
        hours = remaining.total_seconds() / 3600
        if hours >= 1:
            return f"{int(hours)}h {int((hours % 1) * 60)}m"
        else:
            return f"{int(remaining.total_seconds() / 60)}m"
    
    def get_is_valid(self, obj):
        return obj.is_valid()
