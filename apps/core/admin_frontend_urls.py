from django.urls import path
from .admin_frontend_views import (
    AdminLoginView, AdminDashboardView,
    AdminProductListView, AdminProductFormView,
    AdminOrderListView, AdminOrderDetailView,
    AdminUserListView, AdminInventoryView, AdminReportsView,
    AdminCategoryListView, AdminScrollBannerListView, AdminMainBannerListView, AdminPromotionListView,
    AdminCustomizeRequestsListView,
    AdminPromoCodeListView
)

urlpatterns = [
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    
    # Products
    path('admin/products/', AdminProductListView.as_view(), name='admin-products'),
    path('admin/products/add/', AdminProductFormView.as_view(), name='admin-product-add'),
    path('admin/products/<uuid:pk>/edit/', AdminProductFormView.as_view(), name='admin-product-edit'),
    path('admin/categories/', AdminCategoryListView.as_view(), name='admin-categories'),
    
    # Orders
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-orders'),
    path('admin/orders/<uuid:pk>/', AdminOrderDetailView.as_view(), name='admin-order-detail'),
    
    # Others
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin/inventory/', AdminInventoryView.as_view(), name='admin-inventory'),
    path('admin/reports/', AdminReportsView.as_view(), name='admin-reports'),
    
    # Marketing
    path('admin/marketing/scroll-banners/', AdminScrollBannerListView.as_view(), name='admin-scroll-banners'),
    path('admin/marketing/main-banners/', AdminMainBannerListView.as_view(), name='admin-main-banners'),
    path('admin/marketing/promotions/', AdminPromotionListView.as_view(), name='admin-promotions'),
    path('admin/marketing/promocodes/', AdminPromoCodeListView.as_view(), name='admin-promocodes'),
    path('admin/customize-requests/', AdminCustomizeRequestsListView.as_view(), name='admin-customize-requests'),
]
