from rest_framework import viewsets, serializers
from apps.products.models import Product, Category, CustomizeRequest
from apps.core.models import AuditLog
from apps.products.serializers import CustomizeRequestSerializer

# Re-export AdminCategoryViewSet as it was likely imported from here
from apps.products.admin_catalog_views import AdminCategoryViewSet, AdminDimensionViewSet

from apps.core.admin_views import IsAdminUser

class AdminProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class AdminProductViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Products (Admin only)
    """
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = AdminProductSerializer
    permission_classes = [IsAdminUser]
    
    def perform_create(self, serializer):
        product = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='PRODUCT_CREATED',
            resource_type='Product',
            resource_id=str(product.id),
            changes={'name': product.name, 'admin_code': product.admin_code},
            reason='Admin creation',
            ip_address=self._get_client_ip(self.request)
        )
        
    def perform_update(self, serializer):
        product = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='PRODUCT_UPDATED',
            resource_type='Product',
            resource_id=str(product.id),
            reason='Admin update',
            ip_address=self._get_client_ip(self.request)
        )
        
    def perform_destroy(self, instance):
        # Soft Delete
        instance.is_archived = True
        instance.save()
        
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='PRODUCT_DELETED',
            resource_type='Product',
            resource_id=str(instance.id),
            reason='Admin soft delete',
            ip_address=self._get_client_ip(self.request)
        )

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class AdminCustomizeRequestViewSet(viewsets.ModelViewSet):
    """
    Manage Customization Requests
    """
    queryset = CustomizeRequest.objects.all().order_by('-created_at')
    serializer_class = CustomizeRequestSerializer
    permission_classes = [IsAdminUser]
    
    def perform_update(self, serializer):
        req = serializer.save()
        # Audit log for status change
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='CUSTOMIZE_REQ_UPDATED',
            resource_type='CustomizeRequest',
            resource_id=str(req.id),
            changes={'status': req.status},
            reason='Admin status update',
            ip_address=self._get_client_ip(self.request)
        )
        
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
