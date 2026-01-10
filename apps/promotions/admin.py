from django.contrib import admin
from .models import PromoCode, PromoUsage

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'valid_from', 'valid_until', 'is_active', 'usage_count')
    list_filter = ('is_active', 'discount_type')
    search_fields = ('code', 'description')

@admin.register(PromoUsage)
class PromoUsageAdmin(admin.ModelAdmin):
    list_display = ('promo', 'user', 'order', 'discount_amount', 'used_at')
    list_filter = ('used_at',)
    search_fields = ('promo__code', 'user__mobile_number', 'order__id')

