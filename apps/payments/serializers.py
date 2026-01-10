from rest_framework import serializers

class CreatePaymentSerializer(serializers.Serializer):
    order_id = serializers.UUIDField(required=True)

class VerifyPaymentSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField(required=True)
    razorpay_payment_id = serializers.CharField(required=True)
    razorpay_signature = serializers.CharField(required=True)
