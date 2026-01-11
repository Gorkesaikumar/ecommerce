"""
Admin Category and Dimension Management
"""
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from apps.products.models import Category, DimensionConfig, Product
from apps.core.models import AuditLog
from django.db import transaction

class IsAdminUser:
    """Reuse from admin_views"""
    pass

class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent', 
                  'subcategories', 'product_count']
    
    def get_subcategories(self, obj):
        return [{'id': c.id, 'name': c.name} for c in obj.subcategories.all()]
    
    def get_product_count(self, obj):
        return obj.products.filter(is_archived=False).count()

class DimensionConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DimensionConfig
        fields = '__all__'
    
    def validate(self, data):
        # Validate ranges
        if data['min_length'] >= data['max_length']:
            raise serializers.ValidationError("min_length must be less than max_length")
        if data['min_breadth'] >= data['max_breadth']:
            raise serializers.ValidationError("min_breadth must be less than max_breadth")
        if data['min_height'] >= data['max_height']:
            raise serializers.ValidationError("min_height must be less than max_height")
        
        if data['price_multiplier'] <= 0:
            raise serializers.ValidationError("price_multiplier must be positive")
        
        return data

class AdminCategoryViewSet(viewsets.ModelViewSet):
    """Category management"""
    from apps.core.admin_views import IsAdminUser
    permission_classes = [IsAdminUser]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def perform_create(self, serializer):
        category = serializer.save()
        
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='CATEGORY_CREATED',
            resource_type='Category',
            resource_id=str(category.id),
            changes={'name': category.name, 'slug': category.slug},
            reason='Admin category creation',
            ip_address=self._get_client_ip(self.request),
            correlation_id=getattr(self.request, 'correlation_id', None)
        )
    
    def perform_update(self, serializer):
        category = serializer.save()
        
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='CATEGORY_UPDATED',
            resource_type='Category',
            resource_id=str(category.id),
            reason='Admin category update',
            ip_address=self._get_client_ip(self.request),
            correlation_id=getattr(self.request, 'correlation_id', None)
        )
    
    def perform_destroy(self, instance):
        # Check 1: Active products exist
        if instance.products.filter(is_archived=False).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cannot delete category with active products")
        
        # Check 2: Any products have been ordered (even if archived)
        # Products with orders have PROTECTED constraint and cannot be deleted
        from apps.orders.models import OrderItem
        products_with_orders = instance.products.filter(
            order_items__isnull=False
        ).distinct()
        
        if products_with_orders.exists():
            from rest_framework.exceptions import ValidationError
            product_names = list(products_with_orders.values_list('name', flat=True)[:3])
            if len(product_names) == 1:
                msg = f"Cannot delete category: product '{product_names[0]}' has been ordered"
            else:
                msg = f"Cannot delete category: {len(products_with_orders)} products have been ordered"
            raise ValidationError(msg)
        
        # Store info before deletion
        category_id = str(instance.id)
        category_name = instance.name
        
        # Delete the category (this will CASCADE delete all products)
        instance.delete()
        
        # Create audit log after successful deletion
        try:
            AuditLog.objects.create(
                user=self.request.user,
                user_mobile=getattr(self.request.user, 'mobile_number', ''),
                user_role=self.request.user.role,
                action='CATEGORY_DELETED',
                resource_type='Category',
                resource_id=category_id,
                changes={'name': category_name},
                reason='Admin category deletion',
                ip_address=self._get_client_ip(self.request),
                correlation_id=getattr(self.request, 'correlation_id', None)
            )
        except Exception as e:
            # Log audit failure but don't fail the deletion
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create audit log for category deletion: {e}")
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class AdminDimensionViewSet(viewsets.ModelViewSet):
    """Dimension configuration management"""
    from apps.core.admin_views import IsAdminUser
    permission_classes = [IsAdminUser]
    queryset = DimensionConfig.objects.all().select_related('product')
    serializer_class = DimensionConfigSerializer
    
    def perform_create(self, serializer):
        config = serializer.save()
        
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='DIMENSION_CONFIG_CREATED',
            resource_type='DimensionConfig',
            resource_id=str(config.id),
            changes={'product': config.product.admin_code},
            reason='Admin dimension config',
            ip_address=self._get_client_ip(self.request),
            correlation_id=getattr(self.request, 'correlation_id', None)
        )
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
