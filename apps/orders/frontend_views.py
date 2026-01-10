from django.views.generic import TemplateView
from django.shortcuts import redirect
from .services import CartService
from .serializers import CartSerializer

class CartFrontendView(TemplateView):
    template_name = 'cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if not self.request.user.is_authenticated and not self.request.session.session_key:
            self.request.session.create()
            
        session_key = self.request.session.session_key
        cart = CartService.get_cart(self.request.user, session_key)
        
        if cart:
            context['cart'] = CartSerializer(cart).data
        else:
            context['cart'] = None
            
        return context

class CheckoutFrontendView(TemplateView):
    template_name = 'checkout.html'

    def dispatch(self, request, *args, **kwargs):
        # Validate Cart
        session_key = request.session.session_key
        cart = CartService.get_cart(request.user, session_key)
        if not cart or not cart.items.exists():
            return redirect('cart-frontend')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_key = self.request.session.session_key
        cart = CartService.get_cart(self.request.user, session_key)
        context['cart'] = CartSerializer(cart).data
        
        if self.request.user.is_authenticated:
            context['saved_addresses'] = self.request.user.addresses.all()
            
        return context

class OrderSuccessFrontendView(TemplateView):
    template_name = 'order-success.html'

class OrderListFrontendView(TemplateView):
    template_name = 'customer/my-orders.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # Use Service or Direct ORM (Direct ORM simpler for frontend views if read-only)
            from .models import Order
            context['orders'] = Order.objects.filter(user=self.request.user).order_by('-created_at')
        return context

class OrderDetailFrontendView(TemplateView):
    template_name = 'customer/order-detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
             from .models import Order
             from django.shortcuts import get_object_or_404
             order = get_object_or_404(Order, id=kwargs['pk'], user=self.request.user)
             context['order'] = order
        return context
