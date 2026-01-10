from rest_framework import serializers
from .models import Payment
from apps.orders.models import Order
from apps.products.models import Product

class RefundSerializer(serializers.Serializer):
    payment_id = serializers.UUIDField(required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    reason = serializers.CharField(max_length=500, required=False)
    
    def validate_payment_id(self, value):
        try:
            payment = Payment.objects.get(id=value)
            if payment.status != Payment.Status.CAPTURED:
                raise serializers.ValidationError("Can only refund captured payments")
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found")

class AdminOrderSerializer(serializers.ModelSerializer):
    user_mobile = serializers.CharField(source='user.mobile_number', read_only=True)
    payment_status = serializers.CharField(source='payment.status', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'user_mobile', 'status', 'total_amount', 'payment_status', 'created_at', 'updated_at']

class AdminOrderDetailSerializer(serializers.ModelSerializer):
    user_mobile = serializers.CharField(source='user.mobile_number', read_only=True)
    payment_details = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'user_mobile', 'status', 'total_amount', 'shipping_address', 
                  'payment_details', 'items_count', 'created_at', 'updated_at']
    
    def get_payment_details(self, obj):
        if hasattr(obj, 'payment'):
            return {
                'status': obj.payment.status,
                'razorpay_order_id': obj.payment.razorpay_order_id,
                'razorpay_payment_id': obj.payment.razorpay_payment_id,
            }
        return None
    
    def get_items_count(self, obj):
        return obj.items.count()

class AdminPaymentSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source='order.id', read_only=True)
    user_mobile = serializers.CharField(source='order.user.mobile_number', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'order_id', 'user_mobile', 'razorpay_order_id', 'razorpay_payment_id',
                  'amount', 'currency', 'status', 'created_at', 'updated_at']

class AdminOrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
    reason = serializers.CharField(max_length=500, required=True)
