from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Count, Q
from .models import Payment
from .admin_serializers import (
    RefundSerializer, AdminOrderSerializer, AdminOrderDetailSerializer,
    AdminPaymentSerializer, AdminOrderStatusUpdateSerializer
)
from apps.orders.models import Order
from apps.products.models import Product
from apps.core.state_machines import validate_order_transition
from .services import RazorpayService
import logging

logger = logging.getLogger('admin_actions')

class IsAdminUser(IsAuthenticated):
    """Custom permission: User must be admin"""
    def has_permission(self, request, view):
        return (super().has_permission(request, view) and 
                request.user.role == 'ADMIN')

class AdminOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin view for all orders"""
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all().select_related('user', 'payment').order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminOrderDetailSerializer
        return AdminOrderSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Admin override for order status with audit trail
        """
        order = self.get_object()
        serializer = AdminOrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        reason = serializer.validated_data['reason']
        
        try:
            validate_order_transition(order, new_status)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = order.status
        order.status = new_status
        order.save()
        
        # Audit log
        logger.warning(
            f"ADMIN_OVERRIDE: Order {order.id} status changed {old_status} -> {new_status}",
            extra={
                'admin_user': request.user.mobile_number,
                'order_id': str(order.id),
                'old_status': old_status,
                'new_status': new_status,
                'reason': reason,
            }
        )
        
        return Response(AdminOrderDetailSerializer(order).data)

class AdminPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin view for payments"""
    permission_classes = [IsAdminUser]
    serializer_class = AdminPaymentSerializer
    queryset = Payment.objects.all().select_related('order__user').order_by('-created_at')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def failed(self, request):
        """Get all failed payments"""
        failed_payments = self.queryset.filter(status=Payment.Status.FAILED)
        page = self.paginate_queryset(failed_payments)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_reconciliation(self, request):
        """Payments in CREATED status for > 1 hour"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff = timezone.now() - timedelta(hours=1)
        pending = self.queryset.filter(
            status=Payment.Status.CREATED,
            created_at__lt=cutoff
        )
        page = self.paginate_queryset(pending)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

class RefundView(APIView):
    """
    Admin-only refund API
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        serializer = RefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payment_id = serializer.validated_data['payment_id']
        payment = get_object_or_404(Payment, id=payment_id)
        
        # Partial or full refund
        refund_amount = serializer.validated_data.get('amount', payment.amount)
        reason = serializer.validated_data.get('reason', 'Admin initiated')
        
        try:
            # Call Razorpay refund API
            client = RazorpayService.get_client()
            refund = client.payment.refund(
                payment.razorpay_payment_id,
                {
                    'amount': int(float(refund_amount) * 100),  # Convert to paise
                    'notes': {'reason': reason}
                }
            )
            
            # Update payment status
            payment.status = Payment.Status.REFUNDED
            payment.save()
            
            # Restore stock
            with transaction.atomic():
                order = payment.order
                for item in order.items.all():
                    product = Product.objects.select_for_update().get(id=item.product.id)
                    product.stock_quantity += item.quantity
                    product.save()
            
            # Audit log (logger for observability)
            logger.warning(
                f"REFUND_ISSUED: Payment {payment.id} refunded",
                extra={
                    'admin_user': request.user.mobile_number,
                    'payment_id': str(payment.id),
                    'order_id': str(payment.order.id),
                    'amount': str(refund_amount),
                    'reason': reason,
                    'razorpay_refund_id': refund['id']
                }
            )
            
            # Immutable audit record in database
            from apps.core.models import AuditLog
            AuditLog.objects.create(
                user=request.user,
                user_mobile=request.user.mobile_number,
                user_role=request.user.role,
                action='PAYMENT_REFUNDED',
                resource_type='Payment',
                resource_id=str(payment.id),
                changes={
                    'amount': str(refund_amount),
                    'razorpay_refund_id': refund['id'],
                    'order_id': str(payment.order.id)
                },
                reason=reason,
                ip_address=self._get_client_ip(request),
                correlation_id=getattr(request, 'correlation_id', None)
            )
            
            return Response({
                'message': 'Refund processed',
                'refund_id': refund['id'],
                'amount': refund_amount
            })
            
        except Exception as e:
            logger.error(f"Refund failed: {e}")
            return Response({
                'error': 'Refund processing failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
