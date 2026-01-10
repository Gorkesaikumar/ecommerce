from django.views.generic import TemplateView
from django.shortcuts import redirect

class CategoriesView(TemplateView):
    template_name = 'categories.html'

class OrderReviewFrontendView(TemplateView):
    template_name = 'order-review.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mock logic: fetch the latest PENDING order for this user/session
        # In real app, order_id passed via URL or Session
        if self.request.user.is_authenticated:
            from .models import Order
            order = Order.objects.filter(user=self.request.user, status='PENDING').last()
            context['order'] = order
        return context
