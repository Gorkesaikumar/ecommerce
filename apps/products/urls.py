from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductListView, ProductDetailView, CalculatePriceView, CustomizeRequestCreateView
from .admin_views import AdminProductViewSet

router = DefaultRouter()
router.register(r'admin/products', AdminProductViewSet, basename='admin-products')
from .admin_views import AdminCategoryViewSet
router.register(r'admin/categories', AdminCategoryViewSet, basename='admin-categories')
from .admin_views import AdminCustomizeRequestViewSet
router.register(r'admin/customize-requests', AdminCustomizeRequestViewSet, basename='admin-customize-requests')

urlpatterns = [
    path('', include(router.urls)),
    path('products', ProductListView.as_view(), name='product-list'),
    path('products/<uuid:pk>', ProductDetailView.as_view(), name='product-detail'),
    path('products/slug/<slug:slug>', ProductDetailView.as_view(lookup_field='slug'), name='product-detail-slug'),
    path('products/<uuid:pk>/calculate-price', CalculatePriceView.as_view(), name='calculate-price'),
    path('products/customize-request', CustomizeRequestCreateView.as_view(), name='customize-request'),
]
