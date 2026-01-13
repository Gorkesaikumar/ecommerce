"""
Notifications URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationTemplateViewSet, NotificationLogViewSet
from .admin_views import AdminSendNotificationView

router = DefaultRouter()
router.register(r'templates', NotificationTemplateViewSet)
router.register(r'logs', NotificationLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('admin/send/', AdminSendNotificationView.as_view(), name='admin-send-notification'),
]
