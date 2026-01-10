from django.db import models
from django.conf import settings
import uuid

class AuditLog(models.Model):
    """
    Immutable audit log for compliance and security.
    Tracks all critical operations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='audit_logs'
    )
    user_mobile = models.CharField(max_length=15, help_text="Snapshot of user mobile")
    user_role = models.CharField(max_length=20)
    
    # What
    action = models.CharField(max_length=100, help_text="Action performed")
    resource_type = models.CharField(max_length=50, help_text="Model name")
    resource_id = models.CharField(max_length=100, help_text="Object ID")
    
    # Details
    changes = models.JSONField(null=True, blank=True, help_text="Before/after state")
    reason = models.TextField(blank=True)
    
    # When & Where
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    correlation_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Metadata
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.timestamp} - {self.user_mobile} - {self.action}"
    
    def save(self, *args, **kwargs):
        # Only allow INSERT, never UPDATE
        if not self._state.adding:
            raise ValueError("Audit logs are immutable and cannot be updated")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise ValueError("Audit logs are immutable and cannot be deleted")
