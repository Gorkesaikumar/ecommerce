from django.views.generic import ListView, DetailView
from .models import Product, Category
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)

class ProductListFrontendView(ListView):
    model = Product
    template_name = 'product-list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.filter(is_archived=False)
        category_slug = self.request.GET.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
            
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

class ProductDetailFrontendView(DetailView):
    model = Product
    template_name = 'product-detail.html'
    context_object_name = 'product'
    
    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
            
        pk = self.kwargs.get('pk')
        slug = self.kwargs.get('slug')
        
        if pk:
            return get_object_or_404(queryset, pk=pk)
        if slug:
            return get_object_or_404(queryset, slug=slug)
        
        raise AttributeError("Detailed view must be called with either an object pk or a slug in the URLconf.")

class CollectionView(ProductListFrontendView):
    template_name = 'product-list.html'
    
    def get_queryset(self):
        qs = Product.objects.filter(is_archived=False)
        slug = self.kwargs.get('slug')
        
        # Alias 'home' to 'home-decor' if needed, or strict filtering
        if slug == 'home':
            slug = 'home-decor'
            
        if slug:
            qs = qs.filter(category__slug=slug)
            
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug')
        if slug == 'home': slug = 'home-decor'
        
        context['current_category_slug'] = slug
        if slug:
            try:
                category = Category.objects.get(slug=slug)
                context['page_title'] = category.name
            except Category.DoesNotExist:
                context['page_title'] = slug.title()
        return context
