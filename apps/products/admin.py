from django.contrib import admin
from .models import Category, Product, DimensionConfig

class DimensionConfigInline(admin.TabularInline):
    model = DimensionConfig
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'admin_code', 'category', 'base_price', 'stock_quantity', 'is_archived')
    list_filter = ('category', 'is_archived', 'created_at')
    search_fields = ('name', 'admin_code', 'description')
    inlines = [DimensionConfigInline]
    prepopulated_fields = {'slug': ('name',)}

