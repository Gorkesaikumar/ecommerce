from django.contrib import admin
from .models import NotificationTemplate, NotificationLog

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'event', 'is_active')
    list_filter = ('type', 'event', 'is_active')
    search_fields = ('name', 'subject')

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'event', 'type', 'status', 'sent_at')
    list_filter = ('status', 'type', 'event', 'sent_at')
    search_fields = ('recipient', 'error_message')

