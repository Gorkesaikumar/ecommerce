from django.urls import path
from .frontend_views import ProductListFrontendView, ProductDetailFrontendView, CustomizeRequestFrontendView

urlpatterns = [
    path('', ProductListFrontendView.as_view(), name='product-list-frontend'),
    path('<uuid:pk>', ProductDetailFrontendView.as_view(), name='product-detail-pk-frontend'),
    path('<slug:slug>', ProductDetailFrontendView.as_view(), name='product-detail-slug-frontend'),
]
