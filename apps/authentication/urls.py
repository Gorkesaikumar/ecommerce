from django.urls import path
from .views import SendOTPView, VerifyOTPView, LogoutView
from .admin_login_view import AdminLoginView
from .profile_views import UserProfileView, AdminUserUpdateView, ChangePasswordView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Customer OTP Authentication
    path('auth/otp/send', SendOTPView.as_view(), name='send-otp'),
    path('auth/otp/verify', VerifyOTPView.as_view(), name='verify-otp'),
    
    # Admin Email+Password Authentication
    path('auth/admin/login', AdminLoginView.as_view(), name='admin-login'),
    
    # Common
    path('auth/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('auth/profile', UserProfileView.as_view(), name='user-profile'),
    path('auth/password/change', ChangePasswordView.as_view(), name='change-password'),
    path('auth/admin/users/<uuid:user_id>/role', AdminUserUpdateView.as_view(), name='admin-user-role'),
]
