from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AddressViewSet, CartView, CartItemView, OrderViewSet, InvoiceView, ApplyCouponView
from .admin_views import AdminOrderViewSet, AdminAnalyticsViewSet

router = DefaultRouter()
router.register(r'admin/analytics', AdminAnalyticsViewSet, basename='admin-analytics')
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'orders', OrderViewSet, basename='order')
# Note: admin/orders is registered in payments/urls.py with fuller functionality

urlpatterns = [
    path('', include(router.urls)),
    path('cart', CartView.as_view(), name='cart-detail'),
    path('cart/items', CartItemView.as_view(), name='cart-add-item'),
    path('cart/items/<int:pk>', CartItemView.as_view(), name='cart-remove-item'),
    path('cart/apply-coupon', ApplyCouponView.as_view(), name='cart-apply-coupon'),
    path('orders/<uuid:order_id>/invoice', InvoiceView.as_view(), name='order-invoice'),
]
