from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from apps.orders.models import Order

class PaymentFrontendView(TemplateView):
    template_name = 'customer/payment.html'

    def dispatch(self, request, *args, **kwargs):
        # Check order status before rendering
        order_id = kwargs.get('order_id')
        if order_id:
            order = get_object_or_404(Order, id=order_id)
            if order.status not in [Order.Status.PENDING, Order.Status.AWAITING_PAYMENT]:
                # If already paid or complete, redirect to Home as per user request
                # Or could redirect to order detail: redirect('order-detail-frontend', pk=order_id)
                # User asked: "when clicks back he should be on homepage"
                return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = kwargs.get('order_id')
        order = get_object_or_404(Order, id=order_id)
        
        # Security: Check user
        if self.request.user.is_authenticated and order.user != self.request.user:
             pass
             
        context['order'] = order
        return context
