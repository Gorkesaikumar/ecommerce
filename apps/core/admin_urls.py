from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.core.admin_views import (
    AdminReportsView, AdminDashboardView, AdminInventoryViewSet,
    AdminCustomerViewSet, AdminExportView
)
from apps.products.admin_catalog_views import AdminCategoryViewSet, AdminDimensionViewSet
from apps.products.admin_views import AdminProductViewSet

router = DefaultRouter()
router.register(r'inventory', AdminInventoryViewSet, basename='admin-inventory')
router.register(r'customers', AdminCustomerViewSet, basename='admin-customers')
router.register(r'categories', AdminCategoryViewSet, basename='admin-categories')
router.register(r'dimensions', AdminDimensionViewSet, basename='admin-dimensions')
router.register(r'products', AdminProductViewSet, basename='admin-products')

urlpatterns = [
    path('', include(router.urls)),
    path('reports', AdminReportsView.as_view(), name='admin-reports'),
    path('dashboard', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('exports', AdminExportView.as_view(), name='admin-exports'),
]
