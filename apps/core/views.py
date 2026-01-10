from django.shortcuts import render
from django.views.generic import TemplateView
from apps.products.models import Product

class HomeView(TemplateView):
    template_name = 'homepage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch 4 products for "Best Sellers"
        # In a real app, this might use a 'sales_count' or 'is_featured' field
        best_sellers = Product.objects.filter(is_archived=False).order_by('-created_at')[:4]
        context['best_sellers'] = best_sellers
        
        # Real Categories with counts
        from apps.products.models import Category
        from django.db.models import Count
        context['categories'] = Category.objects.annotate(product_count=Count('products')).all()
        
        # Marketing Content
        from apps.promotions.models import ScrollBanner, MainBanner, Promotion
        
        context['scroll_banner'] = ScrollBanner.objects.filter(is_active=True, is_deleted=False).order_by('-priority').first()
        context['main_banner'] = MainBanner.objects.filter(is_active=True, is_deleted=False).order_by('-priority').first()
        context['scroll_banner'] = ScrollBanner.objects.filter(is_active=True, is_deleted=False).order_by('-priority').first()
        context['main_banner'] = MainBanner.objects.filter(is_active=True, is_deleted=False).order_by('-priority').first()
        context['promotions'] = Promotion.objects.filter(is_active=True, is_deleted=False).order_by('-priority')
        
        return context

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
from django.conf import settings
import os
import uuid

class UploadImageAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        if 'file' not in request.data:
            return Response({'error': 'No file provided'}, status=400)
        
        file_obj = request.data['file']
        
        # Validation checks
        if not file_obj.content_type.startswith('image/'):
            return Response({'error': 'File must be an image'}, status=400)
            
        if file_obj.size > 100 * 1024: # 100KB limit
            return Response({'error': 'File size exceeds 100KB limit'}, status=400)
            
        # Generate unique filename
        ext = os.path.splitext(file_obj.name)[1]
        filename = f"uploads/{uuid.uuid4()}{ext}"
        
        # Save
        file_path = default_storage.save(filename, file_obj)
        file_url = os.path.join(settings.MEDIA_URL, file_path).replace('\\', '/')
        
        return Response({'url': file_url})
