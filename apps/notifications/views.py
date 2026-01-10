"""
Notifications Views (Admin only for template management usually)
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from .models import NotificationTemplate, NotificationLog
from .serializers import NotificationTemplateSerializer, NotificationLogSerializer

class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdminUser]

class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NotificationLog.objects.all().order_by('-sent_at')
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAdminUser]
