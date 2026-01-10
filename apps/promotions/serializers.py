from rest_framework import serializers
from .models import ScrollBanner, MainBanner, Promotion

class ScrollBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrollBanner
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_deleted']

class MainBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainBanner
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_deleted']

class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_deleted']

class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import PromoCode
        model = PromoCode
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'usage_count']
