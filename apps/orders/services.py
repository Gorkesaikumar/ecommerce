"""
Order Services - Invoicing and Cart Management
"""
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Cart, CartItem, Order
from django.db import transaction
import uuid

class InvoiceService:
    @staticmethod
    def generate_invoice_html(order: Order) -> str:
        """
        Generates a professional HTML invoice for an order.
        Frontend can print this to PDF.
        """
        # Calculate tax breakdown if not already present
        # For now, we simulate the context needed for a template
        context = {
            'order': order,
            'items': order.items.all(),
            'generated_at': timezone.now(),
            'company_name': 'WoodCraft Ecommerce',
            'gstin': '36AAAAA0000A1Z5', # Example
            'support_email': 'support@woodcraft.com',
            'support_phone': '+91 98765 43210'
        }
        
        # In a real app, use a proper Django template
        # Here we construct a basic HTML string for demonstration/MVP
        invoice_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; padding: 20px; }}
                .header {{ display: flex; justify-content: space-between; margin-bottom: 40px; }}
                .title {{ font-size: 24px; font-weight: bold; }}
                .meta {{ text-align: right; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                th, td {{ padding: 10px; border-bottom: 1px solid #ddd; text-align: left; }}
                th {{ background-color: #f8f8f8; }}
                .totals {{ float: right; width: 300px; }}
                .total-row {{ display: flex; justify-content: space-between; padding: 5px 0; }}
                .grand-total {{ font-weight: bold; font-size: 18px; border-top: 2px solid #333; margin-top: 10px; pt: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div>
                    <div class="title">INVOICE</div>
                    <div>{context['company_name']}</div>
                    <div>GSTIN: {context['gstin']}</div>
                </div>
                <div class="meta">
                    <div>Invoice #: INV-{str(order.id)[:8]}</div>
                    <div>Date: {order.created_at.strftime('%Y-%m-%d')}</div>
                    <div>Status: {order.status}</div>
                </div>
            </div>
            
            <div style="margin-bottom: 30px;">
                <strong>Bill To:</strong><br>
                {order.shipping_address.get('line1')},<br>
                {order.shipping_address.get('city')}, {order.shipping_address.get('state')} - {order.shipping_address.get('zip_code')}
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Qty</th>
                        <th>Price</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in context['items']:
            invoice_html += f"""
                <tr>
                    <td>{item.product.name} ({item.length}x{item.breadth}x{item.height})</td>
                    <td>{item.quantity}</td>
                    <td>₹{item.unit_price}</td>
                    <td>₹{item.unit_price * item.quantity}</td>
                </tr>
            """
            
        invoice_html += f"""
                </tbody>
            </table>
            
            <div class="totals">
                <div class="total-row grand-total">
                    <span>Grand Total:</span>
                    <span>₹{order.total_amount}</span>
                </div>
            </div>
            
            <div style="clear: both; margin-top: 50px; font-size: 12px; color: #666;">
                <p>Thank you for your business!</p>
                <p>For support, contact {context['support_email']} or {context['support_phone']}</p>
            </div>
        </body>
        </html>
        """
        return invoice_html

class CartService:
    @staticmethod
    def get_cart(user, session_key=None):
        """
        Get cart for user OR session. 
        Merges guest cart into user cart on login.
        """
        if user and user.is_authenticated:
            # Check if user has a cart
            cart, created = Cart.objects.get_or_create(user=user)
            
            # Check if there was a guest cart (if session_key provided)
            if session_key:
                try:
                    guest_cart = Cart.objects.get(session_key=session_key, user__isnull=True)
                    # Merge logic
                    CartService.merge_carts(guest_cart, cart)
                except Cart.DoesNotExist:
                    pass
            return cart
        elif session_key:
            cart, created = Cart.objects.get_or_create(session_key=session_key, user__isnull=True)
            return cart
        else:
            # Create a new guest cart if no session key (should normally be provided)
            # This case depends on how the view handles generating session keys
            return None

    @staticmethod
    def merge_carts(guest_cart, user_cart):
        """
        Move items from guest cart to user cart
        """
        with transaction.atomic():
            for item in guest_cart.items.all():
                # Check if item exists in user cart
                existing = user_cart.items.filter(
                    product=item.product,
                    length=item.length,
                    breadth=item.breadth,
                    height=item.height
                ).first()
                
                if existing:
                    existing.quantity += item.quantity
                    existing.save()
                else:
                    item.cart = user_cart
                    item.save()
            
            # Delete guest cart
            guest_cart.delete()
