"""
Order State Machine

Valid State Transitions:
PENDING -> AWAITING_PAYMENT (when Razorpay order created)
AWAITING_PAYMENT -> PAID (when payment captured)
AWAITING_PAYMENT -> PENDING (payment failed, allow retry)
PAID -> SHIPPED
SHIPPED -> DELIVERED
Any -> CANCELLED (admin action)
"""

ALLOWED_ORDER_TRANSITIONS = {
    'PENDING': ['AWAITING_PAYMENT', 'CANCELLED'],
    'AWAITING_PAYMENT': ['PAID', 'PENDING', 'CANCELLED'],
    'PAID': ['SHIPPED', 'CANCELLED'],
    'SHIPPED': ['DELIVERED', 'CANCELLED'],
    'DELIVERED': [],  # Terminal state
    'CANCELLED': [],  # Terminal state
}

def can_transition_order(from_status, to_status):
    """Check if order status transition is valid"""
    return to_status in ALLOWED_ORDER_TRANSITIONS.get(from_status, [])

def validate_order_transition(order, new_status):
    """Raise exception if transition is invalid"""
    if not can_transition_order(order.status, new_status):
        raise ValueError(
            f"Invalid order state transition: {order.status} -> {new_status}"
        )

"""
Payment State Machine

Valid Transitions:
CREATED -> CAPTURED (successful payment)
CREATED -> FAILED (payment rejected)
CAPTURED -> REFUNDED (refund issued)
"""

ALLOWED_PAYMENT_TRANSITIONS = {
    'CREATED': ['CAPTURED', 'FAILED'],
    'CAPTURED': ['REFUNDED'],
    'FAILED': [],  # Terminal
    'REFUNDED': []  # Terminal
}

def can_transition_payment(from_status, to_status):
    """Check if payment status transition is valid"""
    return to_status in ALLOWED_PAYMENT_TRANSITIONS.get(from_status, [])

def validate_payment_transition(payment, new_status):
    """Raise exception if transition is invalid"""
    if not can_transition_payment(payment.status, new_status):
        raise ValueError(
            f"Invalid payment state transition: {payment.status} -> {new_status}"
        )
