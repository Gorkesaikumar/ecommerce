"""
Taxation URL patterns
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaxCategoryViewSet, CalculateCartTaxView, CalculateOrderTaxView

router = DefaultRouter()
router.register(r'categories', TaxCategoryViewSet, basename='tax-category')

urlpatterns = [
    path('', include(router.urls)),
    path('cart/calculate/', CalculateCartTaxView.as_view(), name='calculate-cart-tax'),
    path('order/<uuid:order_id>/breakdown/', CalculateOrderTaxView.as_view(), name='order-tax-breakdown'),
]
