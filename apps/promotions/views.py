"""
Promotions API Views
"""
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import PromoCode
from .services import PromotionService
from rest_framework import serializers

class ValidatePromoSerializer(serializers.Serializer):
    code = serializers.CharField()
    order_amount = serializers.DecimalField(max_digits=10, decimal_places=2)

class ValidatePromoView(APIView):
    """
    Check if a promo code is valid for a cart value
    """
    permission_classes = [AllowAny] # Allow guests to check promos
    
    def post(self, request):
        serializer = ValidatePromoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        amount = serializer.validated_data['order_amount']
        user = request.user if request.user.is_authenticated else None
        
        result = PromotionService.validate_promo_code(code, user, amount)
        
        if not result['valid']:
            return Response({'valid': False, 'message': result['message']}, status=status.HTTP_400_BAD_REQUEST)
            

from rest_framework import permissions, filters, generics
from django.utils import timezone
from .models import Popup
from .serializers import PopupSerializer


class PublicPopupListView(generics.ListAPIView):
    """
    Public Read-Only Popups
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PopupSerializer
    
    def get_queryset(self):
        now = timezone.now()
        queryset = Popup.objects.filter(
            is_active=True,
            start_date__lte=now
        ).order_by('-priority', '-created_at')
        
        # Manually filter end_date since it can be null
        # (Django exclude(end_date__lt=now) would exclude nulls if not careful, 
        # normally exclude doesn't exclude nulls unless condition matches, but let's be safe)
        # Actually Q objects are better: Q(end_date__gte=now) | Q(end_date__isnull=True)
        from django.db.models import Q
        queryset = queryset.filter(Q(end_date__gte=now) | Q(end_date__isnull=True))
        
        return queryset
