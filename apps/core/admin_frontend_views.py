from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'ADMIN'
    
    def handle_no_permission(self):
        return redirect('admin-login')

class AdminLoginView(TemplateView):
    template_name = 'admin/admin-login.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'ADMIN':
            return redirect('admin-dashboard')
        return super().dispatch(request, *args, **kwargs)

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/admin-dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.orders.models import Order
        from django.contrib.auth import get_user_model
        from django.db.models import Sum
        
        # Stats
        context['total_orders'] = Order.objects.count()
        
        # Calculate revenue (ensure it's not None)
        total_revenue = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        context['revenue'] = total_revenue
        
        context['pending_orders'] = Order.objects.filter(status='PENDING').count()
        context['total_users'] = get_user_model().objects.count()
        
        context['today'] = timezone.now().date()
        context['recent_orders'] = Order.objects.all().order_by('-created_at')[:5]
        return context

class AdminProductListView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/admin-products.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.products.models import Product
        context['products'] = Product.objects.filter(is_archived=False)
        return context

class AdminProductFormView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/admin-product-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk') # Restore pk definition
        
        # Add categories for the dropdown
        from apps.products.models import Product, Category
        context['categories'] = Category.objects.all().order_by('name')

        if pk:
             from django.shortcuts import get_object_or_404
             context['product'] = get_object_or_404(Product, pk=pk)
        
        return context

class AdminOrderListView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/admin-orders.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.orders.models import Order
        context['orders'] = Order.objects.all().order_by('-created_at')
        return context

class AdminOrderDetailView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/admin-order-detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.orders.models import Order
        from django.shortcuts import get_object_or_404
        context['order'] = get_object_or_404(Order, pk=self.kwargs['pk'])
        return context

class AdminUserListView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/admin-users.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.auth import get_user_model
        from django.db.models import Count
        
        User = get_user_model()
        base_qs = User.objects.annotate(order_count=Count('orders'))
        
        # 1. Main List
        if self.request.GET.get('filter') == 'rare':
            # Rare: At least 1 purchase, but less than 3 (infrequent)
            context['users'] = base_qs.filter(order_count__gte=1, order_count__lt=3).order_by('-date_joined')
            context['filter_active'] = 'rare'
        else:
            context['users'] = base_qs.order_by('-date_joined')
        
        # 2. Stats
        context['total_customers'] = User.objects.count()
        # Rare: 1-2 orders
        context['rare_customers'] = base_qs.filter(order_count__gte=1, order_count__lt=3).count()
        
        # 3. Top Customers (Banner) - 3+ orders
        context['top_customers'] = base_qs.filter(order_count__gte=3).order_by('-order_count')[:10]
        
        return context

class AdminInventoryView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/admin-inventory.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.products.models import Product, Category
        context['products'] = Product.objects.filter(is_archived=False).order_by('stock_quantity')
        context['categories'] = Category.objects.all()
        return context

class AdminCategoryListView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/admin-categories.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.products.models import Category
        from django.db.models import Count, Q
        context['categories'] = Category.objects.annotate(
            product_count=Count('products', filter=Q(products__is_archived=False))
        ).all().order_by('name')
        return context

class AdminReportsView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/admin-reports.html'

class AdminScrollBannerListView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/marketing/scroll-banners.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.promotions.models import ScrollBanner
        context['banners'] = ScrollBanner.objects.filter(is_deleted=False).order_by('-priority')
        return context

class AdminMainBannerListView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/marketing/main-banners.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.promotions.models import MainBanner
        context['banners'] = MainBanner.objects.filter(is_deleted=False).order_by('-priority')
        return context

class AdminPromotionListView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/marketing/promotions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.promotions.models import Promotion
        context['promotions'] = Promotion.objects.filter(is_deleted=False).order_by('-priority')
        return context

class AdminPromoCodeListView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/marketing/promocodes.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.promotions.models import PromoCode
        context['promocodes'] = PromoCode.objects.all().order_by('-created_at')
        return context

class AdminPopupListView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/marketing/popups.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.promotions.models import Popup
        context['popups'] = Popup.objects.filter(is_deleted=False).order_by('-priority')
        return context

class AdminCustomizeRequestsListView(AdminRequiredMixin, TemplateView):
    template_name = 'admin/admin-customize-requests.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.products.models import CustomizeRequest
        context['requests'] = CustomizeRequest.objects.select_related('product', 'user').all().order_by('-created_at')
        return context
