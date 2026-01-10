"""
Taxation API Views
"""
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import TaxCategory
from .serializers import TaxCategorySerializer, TaxCalculationRequestSerializer
from .services import TaxCalculationService
from apps.orders.models import Cart
import logging

logger = logging.getLogger(__name__)


class TaxCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Public read-only view of tax categories"""
    queryset = TaxCategory.objects.filter(is_active=True)
    serializer_class = TaxCategorySerializer
    permission_classes = []  # Public


class CalculateCartTaxView(APIView):
    """
    Calculate tax breakdown for current user's cart.
    Requires destination state for accurate calculation.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = TaxCalculationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        destination_state = serializer.validated_data['destination_state']
        
        # Get user's cart
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
        
        # Calculate taxes
        tax_breakdown = TaxCalculationService.calculate_cart_tax(cart, destination_state)
        
        return Response(tax_breakdown)


class CalculateOrderTaxView(APIView):
    """
    Get tax breakdown for an existing order.
    Admin or order owner can access.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):
        from apps.orders.models import Order
        
        order = get_object_or_404(Order, id=order_id)
        
        # Check permission
        if order.user != request.user and request.user.role != 'ADMIN':
            return Response(
                {"error": "Unauthorized"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        tax_breakdown = TaxCalculationService.calculate_order_tax(order)
        return Response(tax_breakdown)
