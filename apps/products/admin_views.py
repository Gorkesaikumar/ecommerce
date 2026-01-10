from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.products.models import Product, DimensionConfig, Category
from apps.products.serializers import ProductSerializer
from apps.core.models import AuditLog
from rest_framework import serializers
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class IsAdminUser(IsAuthenticated):
    """Admin-only permission"""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'ADMIN'

class AdminProductSerializer(serializers.ModelSerializer):
    """Full product serializer for admin including admin_code"""
    category_slug = serializers.CharField(write_only=True, required=False)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False) # Allow write by ID

    class Meta:
        model = Product
        fields = ['id', 'name', 'admin_code', 'category', 'category_slug', 'base_price', 'description', 
                  'image_urls', 'stock_quantity', 'is_archived', 'created_at', 'updated_at']

    dimensions = serializers.ListField(
        child=serializers.DictField(), 
        write_only=True, 
        required=False, 
        help_text="List of dimensions: [{length, breadth, height, price}]"
    )

    class Meta:
        model = Product
        fields = ['id', 'name', 'admin_code', 'category', 'category_slug', 'base_price', 'description', 
                  'image_urls', 'stock_quantity', 'dimensions', 'is_archived', 'created_at', 'updated_at']

    def create(self, validated_data):
        slug = validated_data.pop('category_slug', None)
        dimensions_data = validated_data.pop('dimensions', [])
        
        if slug:
            category = Category.objects.filter(slug=slug).first()
            if category:
                validated_data['category'] = category
            else:
                raise serializers.ValidationError({"category_slug": f"Category with slug '{slug}' not found."})
        
        with transaction.atomic():
            product = super().create(validated_data)
            
            # Create Dimensions
            if dimensions_data:
                from apps.products.models import ProductDimension
                for dim in dimensions_data:
                    ProductDimension.objects.create(
                        product=product,
                        length=dim.get('length'),
                        breadth=dim.get('breadth'),
                        height=dim.get('height'),
                        price=dim.get('price'),
                        is_default=dim.get('is_default', False)
                    )
            
            return product

    def update(self, instance, validated_data):
        slug = validated_data.pop('category_slug', None)
        dimensions_data = validated_data.pop('dimensions', None)
        
        if slug:
            category = Category.objects.filter(slug=slug).first()
            if category:
                validated_data['category'] = category
            else:
                 raise serializers.ValidationError({"category_slug": f"Category with slug '{slug}' not found."})
        
        with transaction.atomic():
             product = super().update(instance, validated_data)
             
             # Sync Dimensions if provided
             if dimensions_data is not None:
                 from apps.products.models import ProductDimension
                 # Strategy: Clear and Recreate (Simplest for full sync) or Smart Update
                 # For admin forms, Clear & Recreate is usually safer/easier
                 instance.dimensions.all().delete()
                 for dim in dimensions_data:
                    ProductDimension.objects.create(
                        product=product,
                        length=dim.get('length'),
                        breadth=dim.get('breadth'),
                        height=dim.get('height'),
                        price=dim.get('price'),
                        is_default=dim.get('is_default', False)
                    )
             return product

class AdminProductViewSet(viewsets.ModelViewSet):
    """Admin CRUD for products"""
    permission_classes = [IsAdminUser]
    serializer_class = AdminProductSerializer
    queryset = Product.objects.all()
    
    def perform_create(self, serializer):
        product = serializer.save()
        # Audit log
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='PRODUCT_CREATED',
            resource_type='Product',
            resource_id=str(product.id),
            changes={'admin_code': product.admin_code, 'name': product.name},
            reason='Admin product creation',
            ip_address=self._get_client_ip(self.request),
            correlation_id=getattr(self.request, 'correlation_id', None)
        )
        logger.info(f"Admin {self.request.user.mobile_number} created product {product.admin_code}")
    
    def perform_update(self, serializer):
        old_data = {
            'name': serializer.instance.name,
            'base_price': str(serializer.instance.base_price),
            'stock': serializer.instance.stock_quantity
        }
        product = serializer.save()
        new_data = {
            'name': product.name,
            'base_price': str(product.base_price),
            'stock': product.stock_quantity
        }
        
        # Audit log
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='PRODUCT_UPDATED',
            resource_type='Product',
            resource_id=str(product.id),
            changes={'old': old_data, 'new': new_data},
            reason='Admin product update',
            ip_address=self._get_client_ip(self.request),
            correlation_id=getattr(self.request, 'correlation_id', None)
        )
    
    def perform_destroy(self, instance):
        # Soft delete by archiving
        instance.is_archived = True
        instance.save()
        
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='PRODUCT_ARCHIVED',
            resource_type='Product',
            resource_id=str(instance.id),
            changes={'admin_code': instance.admin_code},
            reason='Admin archival',
            ip_address=self._get_client_ip(self.request),
            correlation_id=getattr(self.request, 'correlation_id', None)
        )
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='products.count', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'product_count']

class AdminCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    
    def perform_create(self, serializer):
        cat = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='CATEGORY_CREATED',
            resource_type='Category',
            resource_id=str(cat.id),
            changes={'name': cat.name},
            ip_address=self._get_client_ip(self.request)
        )

    def perform_update(self, serializer):
        cat = serializer.save()
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='CATEGORY_UPDATED',
            resource_type='Category',
            resource_id=str(cat.id),
            changes={'name': cat.name},
            ip_address=self._get_client_ip(self.request)
        )

    def perform_destroy(self, instance):
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='CATEGORY_DELETED',
            resource_type='Category',
            resource_id=str(instance.id),
            changes={'name': instance.name},
            ip_address=self._get_client_ip(self.request)
        )
        instance.delete()
    
    def _get_client_ip(self, request):
         x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
         if x_forwarded_for:
             return x_forwarded_for.split(',')[0]
         return request.META.get('REMOTE_ADDR')

class AdminCustomizeRequestSerializer(serializers.ModelSerializer):
    """Full serializer for admin view of customize requests"""
    class Meta:
        from apps.products.models import CustomizeRequest
        model = CustomizeRequest
        fields = '__all__'

class AdminCustomizeRequestViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for Customize Requests (Read and Update status)"""
    permission_classes = [IsAdminUser]
    serializer_class = AdminCustomizeRequestSerializer
    
    def get_queryset(self):
        from apps.products.models import CustomizeRequest
        return CustomizeRequest.objects.all().order_by('-created_at')
    
    def perform_update(self, serializer):
        instance = serializer.save()
        # Should probably log audit here too
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action='CUSTOMIZER_REQ_UPDATED',
            resource_type='CustomizeRequest',
            resource_id=str(instance.id),
            changes={'status': instance.status},
            ip_address=self._get_client_ip(self.request)
        )
    
    def _get_client_ip(self, request):
         x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
         if x_forwarded_for:
             return x_forwarded_for.split(',')[0]
         return request.META.get('REMOTE_ADDR')
