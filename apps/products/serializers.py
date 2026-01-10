from rest_framework import serializers
from .models import Product, Category, DimensionConfig, ProductDimension
from decimal import Decimal

class ProductDimensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDimension
        fields = ['length', 'breadth', 'height', 'price', 'is_default']

class DimensionConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DimensionConfig
        fields = ['min_length', 'max_length', 'min_breadth', 'max_breadth', 'min_height', 'max_height']

class ProductSerializer(serializers.ModelSerializer):
    dimension_configs = DimensionConfigSerializer(many=True, read_only=True)
    dimensions = ProductDimensionSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'slug', 'name', 'category', 'category_name', 
            'base_price', 'image_urls', 'description', 
            'dimension_configs', 'dimensions', 'stock_quantity'
        ]
        # admin_code is intentionally excluded from public API

class CalculatePriceSerializer(serializers.Serializer):
    length = serializers.FloatField(min_value=1)
    breadth = serializers.FloatField(min_value=1)
    height = serializers.FloatField(min_value=1)

class CustomizeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import CustomizeRequest
        model = CustomizeRequest
        fields = ['product', 'name', 'email', 'phone', 'length', 'breadth', 'height', 'message']
    
    def validate(self, data):
        if data['length'] <= 0 or data['breadth'] <= 0 or data['height'] <= 0:
            raise serializers.ValidationError("Dimensions must be positive values.")
        return data
