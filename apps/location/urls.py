from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VerifyLocationView, LocationStatusView, ServiceAreasPublicView,
    AdminServiceAreaViewSet, AdminLocationAttemptsView
)

router = DefaultRouter()
router.register(r'admin/service-areas', AdminServiceAreaViewSet, basename='admin-service-areas')

urlpatterns = [
    path('', include(router.urls)),
    path('location/verify', VerifyLocationView.as_view(), name='verify-location'),
    path('location/status', LocationStatusView.as_view(), name='location-status'),
    path('location/service-areas', ServiceAreasPublicView.as_view(), name='service-areas'),
    path('admin/location-attempts', AdminLocationAttemptsView.as_view(), name='admin-location-attempts'),
]
