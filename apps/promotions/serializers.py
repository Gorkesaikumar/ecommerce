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

class PopupSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import Popup
        model = Popup
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_deleted']

    def validate_image(self, value):
        if value:
            if value.size > 100 * 1024: # 100KB limit
                raise serializers.ValidationError("Image size must be under 100KB.")
        return value
