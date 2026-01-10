"""
Shipping API Views
"""
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import ShippingZone, ShippingMethod
from .serializers import (
    ShippingZoneSerializer, ShippingMethodSerializer,
    ShippingEstimateRequestSerializer, PincodeCheckSerializer
)
from .services import ShippingService
from apps.orders.models import Cart
import logging

logger = logging.getLogger(__name__)


class ShippingMethodListView(APIView):
    """
    List available shipping methods (public)
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        methods = ShippingService.get_available_methods()
        return Response(methods)


class CheckPincodeView(APIView):
    """
    Check if a pincode is serviceable
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PincodeCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        pincode = serializer.validated_data['pincode']
        result = ShippingService.check_serviceability(pincode)
        
        return Response(result)


class EstimateShippingView(APIView):
    """
    Estimate shipping cost for given order value and destination
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ShippingEstimateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        estimate = ShippingService.calculate_shipping(
            order_value=data['order_value'],
            destination_state=data['destination_state'],
            weight_kg=data.get('weight_kg', 1),
            shipping_method_code=data.get('shipping_method', 'STANDARD'),
            pincode=data.get('pincode')
        )
        
        return Response(estimate)


class CartShippingEstimateView(APIView):
    """
    Estimate shipping for authenticated user's cart
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ShippingEstimateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        try:
            cart = Cart.objects.prefetch_related('items__product').get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if cart.items.count() == 0:
            return Response(
                {"error": "Cart has no items"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        estimate = ShippingService.estimate_for_cart(
            cart=cart,
            destination_state=data['destination_state'],
            pincode=data.get('pincode')
        )
        
        return Response(estimate)
