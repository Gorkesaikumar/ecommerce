from django.contrib import admin
from .models import Address, Order, OrderItem, Cart, CartItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_snapshot', 'length', 'breadth', 'height', 'unit_price', 'quantity')
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'guest_phone', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'user__mobile_number', 'guest_email', 'guest_phone')
    inlines = [OrderItemInline]
    readonly_fields = ('total_amount', 'shipping_address')

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'state', 'zip_code', 'is_default')
    search_fields = ('user__mobile_number', 'zip_code', 'city')

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key', 'created_at', 'updated_at')
    inlines = [CartItemInline]

