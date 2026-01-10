from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreateRazorpayOrderView, VerifyPaymentView
from .webhooks import RobustRazorpayWebhookView
from .admin_views import AdminOrderViewSet, AdminPaymentViewSet, RefundView
from .frontend_views import PaymentFrontendView

router = DefaultRouter()
router.register(r'admin/orders', AdminOrderViewSet, basename='admin-orders')
router.register(r'admin/payments', AdminPaymentViewSet, basename='admin-payments')

urlpatterns = [
    path('', include(router.urls)),
    path('razorpay/init', CreateRazorpayOrderView.as_view(), name='payment-init'),
    path('razorpay/verify', VerifyPaymentView.as_view(), name='payment-verify'),
    path('razorpay/webhook', RobustRazorpayWebhookView.as_view(), name='payment-webhook'),
    path('admin/refund', RefundView.as_view(), name='admin-refund'),
    # Frontend
    path('checkout/<uuid:order_id>/payment/', PaymentFrontendView.as_view(), name='payment-page'),
]
