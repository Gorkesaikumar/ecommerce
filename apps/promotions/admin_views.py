from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import ScrollBanner, MainBanner, Promotion, PromoCode
from .serializers import ScrollBannerSerializer, MainBannerSerializer, PromotionSerializer, PromoCodeSerializer
from apps.core.models import AuditLog

class IsAdminUser(IsAuthenticated):
    def has_permission(self, request, view):
        has_auth = super().has_permission(request, view)
        print(f"DEBUG: Permission Check | User: {request.user} | Auth: {has_auth} | Superuser: {getattr(request.user, 'is_superuser', False)} | Path: {request.path}")
        # Allow if role is ADMIN *OR* is_superuser
        return has_auth and (request.user.role == 'ADMIN' or request.user.is_superuser)

class BaseMarketingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]

    def _log_action(self, action, resource_name, resource_id, details=None):
        AuditLog.objects.create(
            user=self.request.user,
            user_mobile=self.request.user.mobile_number,
            user_role=self.request.user.role,
            action=action,
            resource_type=resource_name,
            resource_id=str(resource_id),
            changes=details or {},
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

    def perform_create(self, serializer):
        obj = serializer.save()
        self._log_action('CREATE', self.get_queryset().model.__name__, obj.id, serializer.data)

    def perform_update(self, serializer):
        obj = serializer.save()
        self._log_action('UPDATE', self.get_queryset().model.__name__, obj.id, serializer.data)

    def perform_destroy(self, instance):
        # Soft Delete
        instance.is_deleted = True
        instance.is_active = False 
        instance.save()
        self._log_action('DELETE', self.get_queryset().model.__name__, instance.id, {'is_deleted': True})

class AdminScrollBannerViewSet(BaseMarketingViewSet):
    serializer_class = ScrollBannerSerializer
    queryset = ScrollBanner.objects.filter(is_deleted=False).order_by('-priority')

class AdminMainBannerViewSet(BaseMarketingViewSet):
    serializer_class = MainBannerSerializer
    queryset = MainBanner.objects.filter(is_deleted=False).order_by('-priority')

class AdminPromotionViewSet(BaseMarketingViewSet):
    serializer_class = PromotionSerializer
    queryset = Promotion.objects.filter(is_deleted=False).order_by('-priority')

    def create(self, request, *args, **kwargs):
        is_bulk = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=is_bulk)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        # Handle both single and list
        if isinstance(serializer.validated_data, list):
            objs = serializer.save()
            for obj in objs:
                self._log_action('CREATE', self.get_queryset().model.__name__, obj.id, serializer.data)
        else:
            super().perform_create(serializer)

class AdminPromoCodeViewSet(BaseMarketingViewSet):
    serializer_class = PromoCodeSerializer
    queryset = PromoCode.objects.all().order_by('-created_at')

    def perform_destroy(self, instance):
        # Hard delete
        instance.delete()
        self._log_action('DELETE', 'PromoCode', instance.id)

class AdminPopupViewSet(BaseMarketingViewSet):
    from .models import Popup
    from .serializers import PopupSerializer
    serializer_class = PopupSerializer
    queryset = Popup.objects.all() # Inherits soft delete logic if I implement it, wait. Popup doesn't seem to have soft delete in my definition?
    # Checked models.py: Popup inherits MarketingContent. MarketingContent HAS is_deleted.
    # BaseMarketingViewSet perform_destroy does soft delete.
    # So I should filter queryset by is_deleted=False?
    # BaseMarketingViewSet uses get_queryset().model.__name__ which is fine.
    
    queryset = Popup.objects.filter(is_deleted=False).order_by('-priority')
