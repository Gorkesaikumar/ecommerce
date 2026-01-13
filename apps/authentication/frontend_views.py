from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib.auth import logout

class LoginFrontendView(TemplateView):
    template_name = 'customer/login.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

class OTPVerifyFrontendView(TemplateView):
    template_name = 'customer/otp-verify.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

class LogoutView(TemplateView):
    def get(self, request):
        logout(request)
        response = redirect('home')
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

class DashboardFrontendView(TemplateView):
    template_name = 'customer/customer-dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            from apps.orders.models import Order
            from apps.orders.models import Address
            context['orders_count'] = Order.objects.filter(user=self.request.user).count()
            context['addresses_count'] = Address.objects.filter(user=self.request.user).count()
        else:
            context['orders_count'] = 0
            context['addresses_count'] = 0
        return context

class ProfileFrontendView(TemplateView):
    template_name = 'customer/profile.html'

class AddressesFrontendView(TemplateView):
    template_name = 'customer/addresses.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['addresses'] = self.request.user.addresses.all()
        return context
