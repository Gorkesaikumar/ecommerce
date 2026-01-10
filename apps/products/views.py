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
    permission_classes = [AllowAny] # Allow non-logged-in users too

    def perform_create(self, serializer):
        # If user is logged in, attach them
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()
