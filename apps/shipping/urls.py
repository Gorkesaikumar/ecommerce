"""
Shipping URLs
"""
from django.urls import path
from .views import (
    ShippingMethodListView, CheckPincodeView, 
    EstimateShippingView, CartShippingEstimateView
)

urlpatterns = [
    path('methods/', ShippingMethodListView.as_view(), name='shipping-methods'),
    path('check-pincode/', CheckPincodeView.as_view(), name='check-pincode'),
    path('estimate/', EstimateShippingView.as_view(), name='shipping-estimate'),
    path('cart-estimate/', CartShippingEstimateView.as_view(), name='cart-shipping-estimate'),
]
