"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from apps.core.health import HealthCheckView
from apps.core.views import HomeView
from apps.products.frontend_views import CollectionView, CustomizeRequestFrontendView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('health', HealthCheckView.as_view(), name='health-check'),
    
    # API Routes
    path('api/v1/', include('apps.authentication.urls')),
    path('api/v1/', include('apps.products.urls')),
    path('api/v1/', include('apps.orders.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/location/', include('apps.location.urls')),
    path('api/v1/taxation/', include('apps.taxation.urls')),
    path('api/v1/shipping/', include('apps.shipping.urls')),
    path('api/v1/promotions/', include('apps.promotions.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/admin/', include('apps.core.admin_urls')),
    
    # Frontend routes
    # Frontend routes
    path('', HomeView.as_view(), name='home'),
    path('support/', TemplateView.as_view(template_name='support.html'), name='support'),
    path('account/customizations/', CustomizeRequestFrontendView.as_view(), name='product-customizations'),
    path('products/', include('apps.products.frontend_urls')),
    path('collection/<slug:slug>', CollectionView.as_view(), name='collection-detail'),
    path('', include('apps.orders.frontend_urls')),
    path('', include('apps.authentication.frontend_urls')),
    path('', include('apps.core.admin_frontend_urls')),
    path('frontend/', include('apps.core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve frontend static files in development
if settings.DEBUG:
    from django.views.static import serve
    urlpatterns += [
        path('frontend/<path:path>', serve, {'document_root': settings.BASE_DIR / 'frontend'}),
        path('assets/<path:path>', serve, {'document_root': settings.BASE_DIR / 'frontend/assets'}),
    ]
