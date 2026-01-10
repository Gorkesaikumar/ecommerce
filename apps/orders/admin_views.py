from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .serializers import OrderSerializer

class IsAdminUser(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'ADMIN'

class AdminOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin view for all orders (read-only - use update_status action for changes)"""
    permission_classes = [IsAdminUser]
    serializer_class = OrderSerializer
    queryset = Order.objects.all().select_related('user', 'payment').order_by('-created_at')

import csv
from django.http import HttpResponse
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, OrderItem

class AdminAnalyticsViewSet(viewsets.ViewSet):
    """
    Analytics & Reporting for Admin Dashboard
    """
    permission_classes = [IsAdminUser]

    def _get_date_range(self, period):
        now = timezone.now()
        if period == 'today':
             return now.replace(hour=0, minute=0, second=0, microsecond=0)
        if period == '7d':
             return now - timedelta(days=7)
        if period == '30d':
             return now - timedelta(days=30)
        if period == '90d':
             return now - timedelta(days=90)
        return None  # All time

    def _get_filtered_queryset(self, period):
        # Valid orders for analytics are usually those confirmed/paid
        # Including PENDING for now so the chart isn't empty if demo data is just PENDING.
        qs = Order.objects.exclude(status='CANCELLED') 
        start_date = self._get_date_range(period)
        if start_date:
            qs = qs.filter(created_at__gte=start_date)
        return qs

    @action(detail=False, methods=['get'])
    def stats(self, request):
        period = request.query_params.get('period', '30d')
        qs = self._get_filtered_queryset(period)

        total_sales = qs.count()
        total_revenue = qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        # Calculate Top Product
        # We need to filter OrderItems by the same date range implicitly by filtering orders
        # But efficiently:
        top_product_data = OrderItem.objects.filter(order__in=qs)\
            .values('product__name')\
            .annotate(qty=Sum('quantity'))\
            .order_by('-qty').first()
        
        top_product = top_product_data['product__name'] if top_product_data else "N/A"
        top_product_qty = top_product_data['qty'] if top_product_data else 0

        return Response({
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'top_product': top_product,
            'top_product_qty': top_product_qty
        })

    @action(detail=False, methods=['get'])
    def charts(self, request):
        period = request.query_params.get('period', '30d')
        qs = self._get_filtered_queryset(period)

        # 1. Sales Trend (Line Chart)
        # Truncate by day for short periods, by month for long periods could be an optimization, but let's stick to Day for now.
        trend_data = qs.annotate(date=TruncDate('created_at'))\
            .values('date')\
            .annotate(revenue=Sum('total_amount'), count=Count('id'))\
            .order_by('date')
        
        # 2. Top Categories (Pie Chart)
        category_data = OrderItem.objects.filter(order__in=qs)\
            .values('product__category__name')\
            .annotate(count=Sum('quantity'))\
            .order_by('-count')[:5]
            
        return Response({
            'trend': list(trend_data),
            'categories': list(category_data)
        })

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export filtered orders to CSV"""
        period = request.query_params.get('period', '30d')
        qs = self._get_filtered_queryset(period).select_related('user')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sales_report_{period}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Order ID', 'Date', 'Customer', 'Status', 'Total Amount', 'Items Count'])

        for order in qs:
            user_str = order.user.email if order.user else (order.guest_email or "Guest")
            writer.writerow([
                str(order.id),
                order.created_at.strftime('%Y-%m-%d %H:%M'),
                user_str,
                order.status,
                order.total_amount,
                order.items.count() # N+1 but acceptable for export of reasonable size, or optimize with annotate
            ])

        return response
