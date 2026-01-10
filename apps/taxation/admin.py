from django.contrib import admin
from .models import TaxCategory, TaxExemption, BusinessTaxInfo

@admin.register(TaxCategory)
class TaxCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'hsn_code', 'igst_rate', 'is_active')
    search_fields = ('name', 'hsn_code')

@admin.register(TaxExemption)
class TaxExemptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'exemption_type', 'exemption_percentage', 'is_active')
    list_filter = ('exemption_type', 'is_active')

@admin.register(BusinessTaxInfo)
class BusinessTaxInfoAdmin(admin.ModelAdmin):
    list_display = ('legal_name', 'trade_name', 'gstin', 'state_code')

