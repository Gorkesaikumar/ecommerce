"""
Sales & Revenue Reporting Service
Provides accurate, real-time financial reports from database
NO CACHING for financial data
"""
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from apps.orders.models import Order
from apps.payments.models import Payment
from decimal import Decimal

class ReportingService:
    
    @staticmethod
    def daily_report(date=None):
        """Generate daily sales report"""
        if date is None:
            date = timezone.now().date()
        elif isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())
        
        return ReportingService._generate_report(start, end, 'Daily')
    
    @staticmethod
    def weekly_report(year, week):
        """Generate weekly sales report"""
        # Get first day of week
        date_str = f'{year}-W{week:02d}-1'
        start = datetime.strptime(date_str, '%Y-W%W-%w')
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        return ReportingService._generate_report(start, end, 'Weekly')
    
    @staticmethod
    def monthly_report(year, month):
        """Generate monthly sales report"""
        start = datetime(year, month, 1)
        # Last day of month
        next_month = start + timedelta(days=32)
        end = datetime(next_month.year, next_month.month, 1) - timedelta(seconds=1)
        
        return ReportingService._generate_report(start, end, 'Monthly')
    
    @staticmethod
    def custom_report(date_from, date_to):
        """Generate custom date range report"""
        if isinstance(date_from, str):
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
        if isinstance(date_to, str):
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
        
        # Set to end of day for date_to
        date_to = datetime.combine(date_to.date(), datetime.max.time())
        
        return ReportingService._generate_report(date_from, date_to, 'Custom')
    
    @staticmethod
    def _generate_report(start, end, period_type):
        """Core reporting logic"""
        # All orders in period
        orders = Order.objects.filter(created_at__range=(start, end))
        
        # Payments in period
        payments = Payment.objects.filter(created_at__range=(start, end))
        
        # Successful payments (CAPTURED)
        successful_payments = payments.filter(status=Payment.Status.CAPTURED)
        failed_payments = payments.filter(status=Payment.Status.FAILED)
        refunded_payments = payments.filter(status=Payment.Status.REFUNDED)
        
        # Aggregations
        total_orders = orders.count()
        total_revenue = successful_payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        refund_total = refunded_payments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        avg_order_value = successful_payments.aggregate(
            avg=Avg('amount')
        )['avg'] or Decimal('0.00')
        
        # Top products by revenue
        from apps.orders.models import OrderItem
        top_products = OrderItem.objects.filter(
            order__created_at__range=(start, end),
            order__status=Order.Status.PAID
        ).values(
            'product__name', 'product__admin_code'
        ).annotate(
            total_revenue=Sum(F('unit_price') * F('quantity')),
            total_quantity=Sum('quantity')
        ).order_by('-total_revenue')[:10]
        
        # Order status breakdown
        status_breakdown = orders.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        return {
            'period_type': period_type,
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
            'summary': {
                'total_orders': total_orders,
                'total_revenue': str(total_revenue),
                'successful_payments': successful_payments.count(),
                'failed_payments': failed_payments.count(),
                'refunded_payments': refunded_payments.count(),
                'refund_total': str(refund_total),
                'net_revenue': str(total_revenue - refund_total),
                'average_order_value': str(avg_order_value),
            },
            'top_products': list(top_products),
            'order_status_breakdown': list(status_breakdown),
            'generated_at': timezone.now().isoformat()
        }
