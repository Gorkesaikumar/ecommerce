from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Product
from .serializers import ProductSerializer, CalculatePriceSerializer
from .services import PricingService
from django.shortcuts import get_object_or_404

from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from apps.location.permissions import HasVerifiedLocation

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(is_archived=False)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    search_fields = ['name', 'category__name']
    filterset_fields = ['category']

    def list(self, request, *args, **kwargs):
        # Cache Strategy: Key strictly depends on Query Params + Global Version
        version = cache.get("product_cache_version", 1)
        # Create a unique key for this specific query
        query_string = request.GET.urlencode()
        cache_key = f"products:list:v{version}:{query_string}"
        
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response)
            
        response = super().list(request, *args, **kwargs)
        
        # Cache for 1 hour (but invalidated by version change immediately)
        cache.set(cache_key, response.data, timeout=3600)
        return response

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [HasVerifiedLocation]
    lookup_field = 'id'

class CalculatePriceView(APIView):
    permission_classes = [HasVerifiedLocation]  # Location required

    def post(self, request, pk):
        product_id = pk
        serializer = CalculatePriceSerializer(data=request.data)
        
        if serializer.is_valid():
            l = serializer.validated_data['length']
            b = serializer.validated_data['breadth']
            h = serializer.validated_data['height']
            
            try:
                result = PricingService.calculate_price(product_id, l, b, h)
                return Response(result, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Product.DoesNotExist:
                return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from .serializers import CustomizeRequestSerializer

class CustomizeRequestCreateView(generics.CreateAPIView):
    serializer_class = CustomizeRequestSerializer
    permission_classes = [IsAuthenticated] # Require login
    
    def perform_create(self, serializer):
        # Enforce Customer Role
        if self.request.user.role != 'CUSTOMER':
             from rest_framework.exceptions import PermissionDenied
             raise PermissionDenied("Only customers can submit customization requests.")
             
        from django.db import transaction
        with transaction.atomic():
            # Save the request linked to user
            serializer.save(user=self.request.user)
            
            # Smart Save: Sync Profile Data (Name, Email, Mobile) if missing
            # This ensures we capture customer details progressively without separate API calls.
            user = self.request.user
            update_fields = []
            
            # 1. Name Sync
            submitted_name = serializer.validated_data.get('name')
            if not user.name and submitted_name:
                user.name = submitted_name
                update_fields.append('name')
            
            # 2. Email Sync (Safe Check)
            submitted_email = serializer.validated_data.get('email')
            if not user.email and submitted_email:
                # INTEGRITY CHECK: Ensure this email isn't already used by another user
                from django.contrib.auth import get_user_model
                User = get_user_model()
                if not User.objects.filter(email=submitted_email).exists():
                    user.email = submitted_email
                    update_fields.append('email')
            
            # 3. Mobile/Phone Sync (Safe Check)
            # 'phone' in serializer maps to 'mobile_number' in User model
            submitted_phone = serializer.validated_data.get('phone')
            if submitted_phone and submitted_phone != user.mobile_number:
                 # Only update if user somehow has a blank/temp mobile (rare, but good for consistency)
                 # Or if we decide to allow updates. Ideally, mobile is the identity, so we handle with care.
                 # Current logic: If user has placeholder or we want to capture secondary?
                 # Requirement says "If profile is missing...". Mobile is rarely missing as it is the login.
                 # We will add logic just in case mobile was blank (e.g. email login future-proofing).
                 if not user.mobile_number:
                     from django.contrib.auth import get_user_model
                     User = get_user_model()
                     if not User.objects.filter(mobile_number=submitted_phone).exists():
                        user.mobile_number = submitted_phone
                        update_fields.append('mobile_number')

            if update_fields:
                user.save(update_fields=update_fields)

class CustomerCustomizeRequestViewSet(generics.ListAPIView, generics.RetrieveAPIView):
    """
    Allow customers to view their own customization requests.
    """
    serializer_class = CustomizeRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from .models import CustomizeRequest
        return CustomizeRequest.objects.filter(user=self.request.user).order_by('-created_at')
