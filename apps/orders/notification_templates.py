"""
Order Lifecycle Notification Templates

Predefined SMS templates for different order statuses.
"""

def get_order_placed_message(order):
    """SMS for Order Placed status."""
    return (
        f"Order #{str(order.id)[:8]} confirmed! "
        f"Total: ₹{order.total_amount}. "
        f"Track: {get_tracking_url(order)}"
    )

def get_order_shipped_message(order):
    """SMS for Order Shipped status."""
    expected_delivery = order.expected_delivery_date.strftime('%d %b') if hasattr(order, 'expected_delivery_date') and order.expected_delivery_date else "soon"
    return (
        f"Order #{str(order.id)[:8]} shipped from manufacturer! "
        f"Expected delivery: {expected_delivery}. "
        f"Track: {get_tracking_url(order)}"
    )

def get_order_out_for_delivery_message(order):
    """SMS for Out for Delivery status."""
    return (
        f"Your order #{str(order.id)[:8]} is out for delivery today! "
        f"Please be available to receive it. "
        f"Track: {get_tracking_url(order)}"
    )

def get_order_delivered_message(order):
    """SMS for Order Delivered status."""
    return (
        f"Order #{str(order.id)[:8]} delivered successfully! "
        f"Thank you for shopping with us. "
        f"Rate your experience: {get_tracking_url(order)}"
    )

def get_tracking_url(order):
    """Generate order tracking URL."""
    from django.conf import settings
    base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:8000')
    return f"{base_url}/orders/{order.id}"
