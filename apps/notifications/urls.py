"""
Notifications URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationTemplateViewSet, NotificationLogViewSet

router = DefaultRouter()
router.register(r'templates', NotificationTemplateViewSet)
router.register(r'logs', NotificationLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
