"""
CSV Export Utility
Generates CSV responses for admin data exports
"""
import csv
from django.http import HttpResponse
from io import StringIO

class CSVExporter:
    
    @staticmethod
    def export_orders(queryset):
        """Export orders to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Order ID', 'Customer Mobile', 'Status', 'Total Amount', 
            'Payment Status', 'Created At', 'Updated At'
        ])
        
        for order in queryset.select_related('user', 'payment'):
            payment_status = order.payment.status if hasattr(order, 'payment') else 'N/A'
            writer.writerow([
                str(order.id),
                order.user.mobile_number,
                order.status,
                str(order.total_amount),
                payment_status,
                order.created_at.isoformat(),
                order.updated_at.isoformat()
            ])
        
        return response
    
    @staticmethod
    def export_customers(queryset):
        """Export customers to CSV"""
        from django.db.models import Count, Sum
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="customers_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'User ID', 'Mobile Number', 'Name', 'Role', 
            'Total Orders', 'Total Spent', 'Date Joined', 'Active'
        ])
        
        for user in queryset.annotate(
            order_count=Count('orders'),
            total_spent=Sum('orders__total_amount')
        ):
            writer.writerow([
                str(user.id),
                user.mobile_number,
                user.name or '',
                user.role,
                user.order_count,
                str(user.total_spent or '0.00'),
                user.date_joined.isoformat(),
                user.is_active
            ])
        
        return response
    
    @staticmethod
    def export_inventory(queryset):
        """Export inventory to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Product ID', 'Admin Code', 'Name', 'Category', 
            'Base Price', 'Stock Quantity', 'Archived', 'Created At'
        ])
        
        for product in queryset.select_related('category'):
            writer.writerow([
                str(product.id),
                product.admin_code,
                product.name,
                product.category.name,
                str(product.base_price),
                product.stock_quantity,
                product.is_archived,
                product.created_at.isoformat()
            ])
        
        return response
    
    @staticmethod
    def export_audit_logs(queryset):
        """Export audit logs to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_logs_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Timestamp', 'User Mobile', 'User Role', 'Action', 
            'Resource Type', 'Resource ID', 'Reason', 'IP Address'
        ])
        
        for log in queryset:
            writer.writerow([
                log.timestamp.isoformat(),
                log.user_mobile,
                log.user_role,
                log.action,
                log.resource_type,
                log.resource_id,
                log.reason or '',
                log.ip_address or ''
            ])
        
        return response
