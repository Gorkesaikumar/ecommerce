from rest_framework import serializers
from .models import Order, OrderItem, Address, Cart, CartItem
from apps.products.serializers import ProductSerializer
from apps.products.services import PricingService

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'line1', 'city', 'state', 'zip_code', 'is_default']
        read_only_fields = ['state']

    def validate_state(self, value):
        if value != 'Telangana':
            raise serializers.ValidationError("We only deliver in Telangana.")
        return value

class CartItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    price_details = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_details', 'length', 'breadth', 'height', 'quantity', 'price_details']
        extra_kwargs = {'product': {'write_only': True}}

    def get_price_details(self, obj):
        try:
            return PricingService.calculate_price(obj.product.id, obj.length, obj.breadth, obj.height)
        except Exception:
            return None

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    applied_promo_code = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'subtotal', 'discount_amount', 'total_price', 'applied_promo_code']

    def get_subtotal(self, obj):
        return self._calculate_subtotal(obj)

    def _calculate_subtotal(self, obj):
        total = 0
        for item in obj.items.all():
            try:
                price_info = PricingService.calculate_price(item.product.id, item.length, item.breadth, item.height)
                total += float(price_info['final_price']) * item.quantity
            except:
                pass
        return total

    def get_discount_amount(self, obj):
        if not obj.applied_promo:
            return 0.0
        
        # Calculate Subtotal
        subtotal = self._calculate_subtotal(obj)
        
        # Simple Validation (avoid heavy DB hits if possible, but basic checks needed)
        # Ideally, we trust the database state, but min_order might have been violated
        if subtotal < obj.applied_promo.min_order_amount:
            return 0.0
        
        # Calculate
        from apps.promotions.services import PromotionService
        from decimal import Decimal
        return PromotionService.calculate_discount(obj.applied_promo, Decimal(str(subtotal)))

    def get_total_price(self, obj):
        subtotal = self._calculate_subtotal(obj)
        discount = self.get_discount_amount(obj)
        return max(0, subtotal - float(discount))

    def get_applied_promo_code(self, obj):
        return obj.applied_promo.code if obj.applied_promo else None

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_snapshot', 'length', 'breadth', 'height', 'unit_price', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'status', 'total_amount', 'shipping_address', 'payment_method', 'created_at', 'items']

    def validate(self, attrs):
        if self.instance and self.instance.status in [Order.Status.CANCELLED, Order.Status.DELIVERED]:
             raise serializers.ValidationError(f"Cannot edit a {self.instance.status} order.")
        return attrs

class CreateOrderSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(required=True)
