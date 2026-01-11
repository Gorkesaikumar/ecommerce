from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ValidatePromoView, PublicPopupListView
from apps.core.views import UploadImageAPIView
from .admin_views import AdminScrollBannerViewSet, AdminMainBannerViewSet, AdminPromotionViewSet, AdminPromoCodeViewSet, AdminPopupViewSet

router = DefaultRouter()
router.register('admin/scroll-banners', AdminScrollBannerViewSet, basename='admin-scroll-banners')
router.register('admin/main-banners', AdminMainBannerViewSet, basename='admin-main-banners')
router.register('admin/promotions', AdminPromotionViewSet, basename='admin-promotions')
router.register('admin/promocodes', AdminPromoCodeViewSet, basename='admin-promocodes')
router.register('admin/popups', AdminPopupViewSet, basename='admin-popups')

urlpatterns = [
    path('', include(router.urls)),
    path('validate/', ValidatePromoView.as_view(), name='validate-promo'),
    path('upload/', UploadImageAPIView.as_view(), name='upload-image'),
    path('public/popups/', PublicPopupListView.as_view(), name='public-popups'),
]
