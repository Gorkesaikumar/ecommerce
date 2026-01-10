"""
Shipping Serializers
"""
from rest_framework import serializers
from .models import ShippingZone, ShippingMethod


class ShippingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingZone
        fields = '__all__'


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = ['id', 'name', 'code', 'description', 'rate_multiplier', 'has_tracking', 'delivery_days_adjustment']


class PincodeCheckSerializer(serializers.Serializer):
    pincode = serializers.RegexField(regex=r'^\d{6}$', error_messages={'invalid': "Enter a valid 6-digit pincode"})


class ShippingEstimateRequestSerializer(serializers.Serializer):
    order_value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    destination_state = serializers.CharField(max_length=100)
    weight_kg = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, default=1.0)
    shipping_method = serializers.CharField(required=False, default='STANDARD')
    pincode = serializers.CharField(min_length=6, max_length=6, required=False)
    
    def validate(self, data):
        # If estimating for cart, order_value might not be passed, handled in view
        if 'order_value' not in data and not self.context.get('is_cart_estimate'):
            # This validation is loose to allow reuse, strictly validated in logic
            pass
        return data
