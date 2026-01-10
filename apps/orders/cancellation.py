from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Order
from .serializers import OrderSerializer
from apps.core.state_machines import validate_order_transition
from apps.core.models import AuditLog
from apps.products.models import Product
import logging

logger = logging.getLogger(__name__)

class OrderCancellationMixin:
    """Mixin to add order cancellation capability"""
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Customer can cancel PENDING or AWAITING_PAYMENT orders
        """
        order = self.get_object()
        
        # Ownership check
        if order.user != request.user:
            return Response({'error': 'Not your order'}, status=status.HTTP_403_FORBIDDEN)
        
        # Status check
        if order.status not in [Order.Status.PENDING, Order.Status.AWAITING_PAYMENT]:
            return Response({
                'error': f'Cannot cancel order in {order.status} status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate transition
        try:
            validate_order_transition(order, Order.Status.CANCELLED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Restore stock if already decremented
        with transaction.atomic():
            if order.status == Order.Status.AWAITING_PAYMENT:
                for item in order.items.all():
                    product = Product.objects.select_for_update().get(id=item.product.id)
                    product.stock_quantity += item.quantity
                    product.save()
                    logger.info(f"Restored {item.quantity} units of {product.name}")
            
            order.status = Order.Status.CANCELLED
            order.save()
            
            # Audit log
            AuditLog.objects.create(
                user=request.user,
                user_mobile=request.user.mobile_number,
                user_role=request.user.role,
                action='ORDER_CANCELLED',
                resource_type='Order',
                resource_id=str(order.id),
                reason='Customer cancellation',
                ip_address=self._get_client_ip(request),
                correlation_id=getattr(request, 'correlation_id', None)
            )
        
        logger.info(f"Order {order.id} cancelled by customer")
        return Response(OrderSerializer(order).data)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
