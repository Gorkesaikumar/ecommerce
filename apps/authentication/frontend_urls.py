from django.urls import path
from .frontend_views import (
    LoginFrontendView, OTPVerifyFrontendView, LogoutView,
    DashboardFrontendView, ProfileFrontendView, AddressesFrontendView
)
from apps.products.frontend_views import CustomizeRequestFrontendView

urlpatterns = [
    path('login/', LoginFrontendView.as_view(), name='login'),
    path('verify-otp/', OTPVerifyFrontendView.as_view(), name='verify-otp'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Account Routes
    path('account/dashboard/', DashboardFrontendView.as_view(), name='dashboard'),
    path('account/profile/', ProfileFrontendView.as_view(), name='profile'),
    path('account/addresses/', AddressesFrontendView.as_view(), name='addresses'),
]
