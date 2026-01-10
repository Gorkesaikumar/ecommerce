from django.urls import path
from .frontend_views import CartFrontendView, CheckoutFrontendView, OrderSuccessFrontendView, OrderListFrontendView, OrderDetailFrontendView
from .frontend_views_extras import OrderReviewFrontendView, CategoriesView

urlpatterns = [
    path('cart/', CartFrontendView.as_view(), name='cart-frontend'),
    path('checkout/', CheckoutFrontendView.as_view(), name='checkout-frontend'),
    path('checkout/review/', OrderReviewFrontendView.as_view(), name='order-review'), # New
    path('checkout/success/', OrderSuccessFrontendView.as_view(), name='order-success-frontend'),
    
    path('categories/', CategoriesView.as_view(), name='categories'), # New

    path('account/orders/', OrderListFrontendView.as_view(), name='order-list-frontend'),
    path('account/orders/<uuid:pk>/', OrderDetailFrontendView.as_view(), name='order-detail-frontend'),
]
