from apps.orders.models import Cart

def cart_count(request):
    """
    Context processor to make cart item count available globally.
    """
    count = 0
    
    # Check if user is authenticated
    if request.user.is_authenticated:
        try:
            # Optimize: use count() or aggregate instead of loading whole cart
            # Assuming OneToOne or ForeignKey named 'cart' (User has one cart)
            # Based on models.py: user = ForeignKey in Cart.
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                # Sum of quantities
                from django.db.models import Sum
                result = cart.items.aggregate(total_qty=Sum('quantity'))
                count = result['total_qty'] or 0
        except:
            pass
            
    # Check Session for Guest
    else:
        session_key = request.session.session_key
        if session_key:
            try:
                cart = Cart.objects.filter(session_key=session_key).first()
                if cart:
                    from django.db.models import Sum
                    result = cart.items.aggregate(total_qty=Sum('quantity'))
                    count = result['total_qty'] or 0
            except:
                pass
                
    return {'cart_item_count': count}
