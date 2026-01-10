from django.contrib import admin
from .models import ServiceArea, CustomerLocation, LocationAttempt

@admin.register(ServiceArea)
class ServiceAreaAdmin(admin.ModelAdmin):
    list_display = ('country', 'state', 'district', 'city', 'is_active')
    list_filter = ('is_active', 'country', 'state')
    search_fields = ('city', 'district', 'state')

@admin.register(CustomerLocation)
class CustomerLocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'state', 'is_verified', 'expires_at')
    list_filter = ('is_verified', 'state')
    search_fields = ('user__mobile_number', 'city', 'full_address')

@admin.register(LocationAttempt)
class LocationAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'was_allowed', 'timestamp', 'city', 'matched_service_area')
    list_filter = ('was_allowed', 'timestamp')
    readonly_fields = ('user', 'latitude', 'longitude', 'accuracy', 'submitted_timestamp', 
                      'city', 'district', 'state', 'country', 'was_allowed', 'denial_reason', 
                      'matched_service_area', 'ip_address', 'user_agent', 'correlation_id')
