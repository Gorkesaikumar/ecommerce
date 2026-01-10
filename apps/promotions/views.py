"""
Promotions API Views
"""
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import PromoCode
from .services import PromotionService
from rest_framework import serializers

class ValidatePromoSerializer(serializers.Serializer):
    code = serializers.CharField()
    order_amount = serializers.DecimalField(max_digits=10, decimal_places=2)

class ValidatePromoView(APIView):
    """
    Check if a promo code is valid for a cart value
    """
    permission_classes = [AllowAny] # Allow guests to check promos
    
    def post(self, request):
        serializer = ValidatePromoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        amount = serializer.validated_data['order_amount']
        user = request.user if request.user.is_authenticated else None
        
        result = PromotionService.validate_promo_code(code, user, amount)
        
        if not result['valid']:
            return Response({'valid': False, 'message': result['message']}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'valid': True,
            'code': result['promo'].code,
            'discount_amount': result['discount_amount'],
            'message': result['message']
        })
