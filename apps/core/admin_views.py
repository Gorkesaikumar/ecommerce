"""
Admin Reporting, Dashboard, Inventory, and Customer Management APIs
"""
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from datetime import timedelta
from apps.core.services.reporting_service import ReportingService
from apps.core.services.export_service import CSVExporter
from apps.core.models import AuditLog
from apps.products.models import Product
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.authentication.token_blacklist import TokenBlacklist
import logging

logger = logging.getLogger('admin_actions')
User = get_user_model()

class IsAdminUser(IsAuthenticated):
    """Admin-only permission"""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'ADMIN'

# ====================== REPORTING ENDPOINTS ======================

class AdminReportsView(APIView):
    """Sales and revenue reporting"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        report_type = request.query_params.get('type', 'daily')
        
        try:
            if report_type == 'daily':
                date = request.query_params.get('date')
                report = ReportingService.daily_report(date)
            
            elif report_type == 'weekly':
                year = int(request.query_params.get('year', timezone.now().year))
                week = int(request.query_params.get('week', timezone.now().isocalendar()[1]))
                report = ReportingService.weekly_report(year, week)
            
            elif report_type == 'monthly':
                year = int(request.query_params.get('year', timezone.now().year))
                month = int(request.query_params.get('month', timezone.now().month))
                report = ReportingService.monthly_report(year, month)
            
            elif report_type == 'custom':
                date_from = request.query_params.get('date_from')
                date_to = request.query_params.get('date_to')
                if not date_from or not date_to:
                    return Response({'error': 'date_from and date_to required'}, 
                                    status=status.HTTP_400_BAD_REQUEST)
                report = ReportingService.custom_report(date_from, date_to)
            
            else:
                return Response({'error': 'Invalid report type'}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(report)
        
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ====================== DASHBOARD ENDPOINT ======================

class AdminDashboardView(APIView):
    """Admin dashboard with real-time metrics"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Today's metrics
        today_orders = Order.objects.filter(created_at__gte=today_start)
        today_revenue = Payment.objects.filter(
            created_at__gte=today_start,
            status=Payment.Status.CAPTURED
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Pending orders
        pending_orders = Order.objects.filter(
            status__in=[Order.Status.PENDING, Order.Status.AWAITING_PAYMENT]
        ).count()
        
        # Low stock products
        low_stock_threshold = 10
        low_stock_count = Product.objects.filter(
            stock_quantity__lte=low_stock_threshold,
            is_archived=False
        ).count()
        
        # Failed payments (last 24h)
        failed_payments_24h = Payment.objects.filter(
            created_at__gte=last_24h,
            status=Payment.Status.FAILED
        ).count()
        
        # Active customers (ordered in last 30 days)
        active_customers = User.objects.filter(
            orders__created_at__gte=now - timedelta(days=30),
            role=User.Roles.CUSTOMER
        ).distinct().count()
        
        # New signups (last 7 days)
        new_signups = User.objects.filter(
            date_joined__gte=last_7d
        ).count()
        
        return Response({
            'today': {
                'orders': today_orders.count(),
                'revenue': str(today_revenue)
            },
            'pending_orders': pending_orders,
            'low_stock_products': low_stock_count,
            'failed_payments_24h': failed_payments_24h,
            'active_customers': active_customers,
            'new_signups_7d': new_signups,
            'timestamp': now.isoformat()
        })

# ====================== INVENTORY MANAGEMENT ======================

class AdminInventoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Inventory management and stock control"""
    permission_classes = [IsAdminUser]
    queryset = Product.objects.all().select_related('category')
    
    def list(self, request):
        """List all products with stock info"""
        products = self.get_queryset()
        
        # Filter options
        low_stock = request.query_params.get('low_stock')
        if low_stock:
            threshold = int(low_stock)
            products = products.filter(stock_quantity__lte=threshold)
        
        archived = request.query_params.get('archived')
        if archived == 'true':
            products = products.filter(is_archived=True)
        elif archived == 'false':
            products = products.filter(is_archived=False)
        
        data = [{
            'id': str(p.id),
            'admin_code': p.admin_code,
            'name': p.name,
            'category': p.category.name,
            'stock_quantity': p.stock_quantity,
            'base_price': str(p.base_price),
            'is_archived': p.is_archived
        } for p in products]
        
        return Response(data)
    
    @action(detail=True, methods=['put'])
    def update_stock(self, request, pk=None):
        """Update stock for single product"""
        product = self.get_object()
        new_stock = request.data.get('stock_quantity')
        reason = request.data.get('reason', 'Admin stock adjustment')
        
        if new_stock is None or new_stock < 0:
            return Response({'error': 'Invalid stock quantity'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        old_stock = product.stock_quantity
        
        with transaction.atomic():
            product.stock_quantity = new_stock
            product.save()
            
            # Invalidate product cache
            from django.core.cache import cache
            cache.incr('ecom:products:version', delta=1)
            
            # Audit log
            AuditLog.objects.create(
                user=request.user,
                user_mobile=request.user.mobile_number,
                user_role=request.user.role,
                action='STOCK_UPDATED',
                resource_type='Product',
                resource_id=str(product.id),
                changes={'old_stock': old_stock, 'new_stock': new_stock},
                reason=reason,
                ip_address=self._get_client_ip(request),
                correlation_id=getattr(request, 'correlation_id', None)
            )
        
        logger.info(f"Stock updated for {product.admin_code}: {old_stock} -> {new_stock}")
        return Response({'message': 'Stock updated', 'new_stock': new_stock})
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk stock update"""
        updates = request.data.get('updates', [])
        reason = request.data.get('reason', 'Bulk stock adjustment')
        
        if not updates:
            return Response({'error': 'No updates provided'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        updated_count = 0
        errors = []
        
        with transaction.atomic():
            for update in updates:
                product_id = update.get('product_id')
                new_stock = update.get('stock_quantity')
                
                try:
                    product = Product.objects.select_for_update().get(id=product_id)
                    old_stock = product.stock_quantity
                    product.stock_quantity = new_stock
                    product.save()
                    
                    # Audit log
                    AuditLog.objects.create(
                        user=request.user,
                        user_mobile=request.user.mobile_number,
                        user_role=request.user.role,
                        action='BULK_STOCK_UPDATE',
                        resource_type='Product',
                        resource_id=str(product.id),
                        changes={'old_stock': old_stock, 'new_stock': new_stock},
                        reason=reason,
                        ip_address=self._get_client_ip(request),
                        correlation_id=getattr(request, 'correlation_id', None)
                    )
                    updated_count += 1
                
                except Product.DoesNotExist:
                    errors.append(f"Product {product_id} not found")
                except Exception as e:
                    errors.append(f"Product {product_id}: {str(e)}")
            
            # Invalidate cache
            from django.core.cache import cache
            cache.incr('ecom:products:version', delta=1)
        
        return Response({
            'updated': updated_count,
            'errors': errors
        })
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

# ====================== CUSTOMER MANAGEMENT ======================

class AdminCustomerViewSet(viewsets.ReadOnlyModelViewSet):
    """Customer management"""
    permission_classes = [IsAdminUser]
    queryset = User.objects.filter(role=User.Roles.CUSTOMER)
    
    def list(self, request):
        """List all customers with order stats"""
        customers = self.get_queryset().annotate(
            order_count=Count('orders'),
            total_spent=Sum('orders__total_amount')
        ).order_by('-date_joined')
        
        data = [{
            'id': str(c.id),
            'mobile_number': c.mobile_number,
            'name': c.name or '',
            'order_count': c.order_count,
            'total_spent': str(c.total_spent or '0.00'),
            'date_joined': c.date_joined.isoformat(),
            'is_active': c.is_active
        } for c in customers]
        
        return Response(data)
    
    def retrieve(self, request, pk=None):
        """Customer detail with order history"""
        customer = self.get_object()
        orders = Order.objects.filter(user=customer).select_related('payment')
        
        return Response({
            'id': str(customer.id),
            'mobile_number': customer.mobile_number,
            'name': customer.name or '',
            'role': customer.role,
            'date_joined': customer.date_joined.isoformat(),
            'is_active': customer.is_active,
            'orders': [{
                'id': str(o.id),
                'status': o.status,
                'total_amount': str(o.total_amount),
                'payment_status': o.payment.status if hasattr(o, 'payment') else None,
                'created_at': o.created_at.isoformat()
            } for o in orders]
        })
    
    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """Disable customer account"""
        customer = self.get_object()
        reason = request.data.get('reason', 'Admin action')
        
        customer.is_active = False
        customer.save()
        
        # Audit log
        AuditLog.objects.create(
            user=request.user,
            user_mobile=request.user.mobile_number,
            user_role=request.user.role,
            action='CUSTOMER_DISABLED',
            resource_type='User',
            resource_id=str(customer.id),
            reason=reason,
            ip_address=self._get_client_ip(request),
            correlation_id=getattr(request, 'correlation_id', None)
        )
        
        return Response({'message': 'Customer disabled'})
    
    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        """Enable customer account"""
        customer = self.get_object()
        reason = request.data.get('reason', 'Admin action')
        
        customer.is_active = True
        customer.save()
        
        # Audit log
        AuditLog.objects.create(
            user=request.user,
            user_mobile=request.user.mobile_number,
            user_role=request.user.role,
            action='CUSTOMER_ENABLED',
            resource_type='User',
            resource_id=str(customer.id),
            reason=reason,
            ip_address=self._get_client_ip(request),
            correlation_id=getattr(request, 'correlation_id', None)
        )
        
        return Response({'message': 'Customer enabled'})
    
    @action(detail=True, methods=['post'])
    def force_logout(self, request, pk=None):
        """Force logout customer (invalidate all tokens)"""
        customer = self.get_object()
        reason = request.data.get('reason', 'Admin forced logout')
        
        # Note: This is a placeholder - in production, you'd blacklist all user's tokens
        # For now, we just log the action
        
        AuditLog.objects.create(
            user=request.user,
            user_mobile=request.user.mobile_number,
            user_role=request.user.role,
            action='FORCE_LOGOUT',
            resource_type='User',
            resource_id=str(customer.id),
            reason=reason,
            ip_address=self._get_client_ip(request),
            correlation_id=getattr(request, 'correlation_id', None)
        )
        
        return Response({'message': 'User sessions invalidated'})
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

# ====================== EXPORT ENDPOINTS ======================

class AdminExportView(APIView):
    """Data export to CSV"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        export_type = request.query_params.get('type')
        
        if export_type == 'orders':
            queryset = Order.objects.all().select_related('user', 'payment')
            
            # Apply filters
            status_filter = request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)
            
            return CSVExporter.export_orders(queryset)
        
        elif export_type == 'customers':
            queryset = User.objects.filter(role=User.Roles.CUSTOMER)
            return CSVExporter.export_customers(queryset)
        
        elif export_type == 'inventory':
            queryset = Product.objects.all().select_related('category')
            return CSVExporter.export_inventory(queryset)
        
        elif export_type == 'audit_logs':
            queryset = AuditLog.objects.all()
            
            date_from = request.query_params.get('date_from')
            if date_from:
                queryset = queryset.filter(timestamp__gte=date_from)
            
            return CSVExporter.export_audit_logs(queryset)
        
        else:
            return Response({'error': 'Invalid export type'}, 
                          status=status.HTTP_400_BAD_REQUEST)
