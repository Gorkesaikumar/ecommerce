from django.contrib import admin
from .models import ShippingZone, ShippingRate, ShippingMethod, PincodeServiceability

class ShippingRateInline(admin.TabularInline):
    model = ShippingRate
    extra = 1

@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority', 'is_active')
    inlines = [ShippingRateInline]
    search_fields = ('name',)

@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'priority', 'is_active', 'rate_multiplier')
    list_filter = ('is_active',)

@admin.register(PincodeServiceability)
class PincodeServiceabilityAdmin(admin.ModelAdmin):
    list_display = ('pincode', 'city', 'state', 'zone', 'is_serviceable')
    list_filter = ('is_serviceable', 'cod_available', 'zone')
    search_fields = ('pincode', 'city')

