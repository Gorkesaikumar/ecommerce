from rest_framework import viewsets, status, generics, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.http import HttpResponse
from .models import Address, Cart, CartItem, Order, OrderItem
from .serializers import AddressSerializer, CartSerializer, CartItemSerializer, OrderSerializer, CreateOrderSerializer
from .services import CartService, InvoiceService
from apps.products.services import PricingService
from apps.products.models import Product
from apps.location.permissions import HasVerifiedLocation
from .cancellation import OrderCancellationMixin
import uuid

class AddressViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CartView(APIView):
    permission_classes = [AllowAny] # Allow guests

    def get_cart(self, request):
        # Helper to get cart based on user or session
        session_key = request.headers.get('X-Session-Key')
        
        if not request.user.is_authenticated and not session_key:
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key
            
        cart = CartService.get_cart(request.user, session_key)
        return cart

    def get(self, request):
        cart = self.get_cart(request)
        if not cart:
             return Response({"items": [], "total": 0})
        serializer = CartSerializer(cart)
        return Response(serializer.data)

class CartItemView(APIView):
    permission_classes = [AllowAny] # Allow guests

    def post(self, request):
        session_key = request.headers.get('X-Session-Key')
        
        if not request.user.is_authenticated and not session_key:
             # Ensure Django session exists for guest persistence
             if not request.session.session_key:
                 request.session.create()
             session_key = request.session.session_key
        
        # Get or create cart via service
        cart = CartService.get_cart(request.user, session_key)
        if not cart:
             # Should practically never happen if service creates it
             return Response({"error": "Could not create cart"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        product_id = request.data.get('product_id')
        length = float(request.data.get('length', 0))
        breadth = float(request.data.get('breadth', 0))
        height = float(request.data.get('height', 0))
        quantity = int(request.data.get('quantity', 1))

        # Validate Dimensions & Price
        try:
            PricingService.calculate_price(product_id, length, breadth, height)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)

        # Add or Update Item
        from django.db.models import F
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            length=length,
            breadth=breadth,
            height=height,
            defaults={'quantity': 0}
        )
        cart_item.quantity = F('quantity') + quantity
        cart_item.save()

        response = Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)
        if hasattr(cart, 'session_key') and cart.session_key   :
             response['X-Session-Key'] = cart.session_key
        return response

    def delete(self, request, pk):
        # Handle deletion securely
        session_key = request.headers.get('X-Session-Key') or request.session.session_key
        
        if request.user.is_authenticated:
            cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        elif session_key:
            cart_item = get_object_or_404(CartItem, pk=pk, cart__session_key=session_key)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
            
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, pk):
        """
        Update Cart Item Quantity
        """
        session_key = request.headers.get('X-Session-Key') or request.session.session_key
        
        if request.user.is_authenticated:
            cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        elif session_key:
            cart_item = get_object_or_404(CartItem, pk=pk, cart__session_key=session_key)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        quantity = int(request.data.get('quantity', 1))
        
        if quantity < 1:
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        # Check Stock
        if cart_item.product.stock_quantity < quantity:
             return Response(
                 {"error": f"Only {cart_item.product.stock_quantity} units available."}, 
                 status=status.HTTP_400_BAD_REQUEST
             )

        cart_item.quantity = quantity
        cart_item.save()
        
        # Return updated cart to refresh UI
        cart = cart_item.cart
        return Response(CartSerializer(cart).data)

class ApplyCouponView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get('code')
        action = request.data.get('action', 'apply') # apply or remove
        
        session_key = request.headers.get('X-Session-Key')
        if not request.user.is_authenticated and not session_key:
             if not request.session.session_key:
                 request.session.create()
             session_key = request.session.session_key
             
        cart = CartService.get_cart(request.user, session_key)
        if not cart:
             return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

        if action == 'remove':
            cart.applied_promo = None
            cart.save()
            return Response(CartSerializer(cart).data)

        if not code:
            return Response({"error": "Code required"}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate Cart Total for validation
        subtotal = 0
        for item in cart.items.all():
            try:
                price_info = PricingService.calculate_price(item.product.id, item.length, item.breadth, item.height)
                subtotal += float(price_info['final_price']) * item.quantity
            except:
                pass
        
        from apps.promotions.services import PromotionService
        from decimal import Decimal
        
        validation = PromotionService.validate_promo_code(code, request.user if request.user.is_authenticated else None, Decimal(str(subtotal)))
        
        if not validation['valid']:
            return Response({"error": validation['message']}, status=status.HTTP_400_BAD_REQUEST)
            
        cart.applied_promo = validation['promo']
        cart.save()
        
        return Response(CartSerializer(cart).data)

class OrderViewSet(OrderCancellationMixin, viewsets.ModelViewSet):
    # permission_classes = [HasVerifiedLocation]
    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only Admin can update/delete arbitrary orders (CancellationMixin handles user cancel)
            from apps.products.admin_views import IsAdminUser
            return [IsAdminUser()]
        return [HasVerifiedLocation()]

    def get_queryset(self):
        # Admin sees all, User sees own
        if self.request.user.role == 'ADMIN':
             return Order.objects.all().order_by('-created_at')
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

    def create(self, request):
        """
        Checkout: Converts Cart -> Order
        """
        # Determine user/guest
        session_key = request.headers.get('X-Session-Key')
        
        # Use simple serializer for address or existing ID
        # For guest, address must be provided in body
        # For user, can use address_id
        
        # We need a unified approach. Let's assume request data has shipping_address (dict) or address_id
        # For simplicity here, reusing CreateOrderSerializer but adapting manual logic below
        
        shipping_address_data = None
        
        if request.user.is_authenticated:
            if 'address_id' in request.data:
                address_id = request.data['address_id']
                address = get_object_or_404(Address, id=address_id, user=request.user)
                shipping_address_data = AddressSerializer(address).data
            elif 'shipping_address' in request.data:
                # Use provided address
                shipping_address_data = request.data['shipping_address']
                
            cart = CartService.get_cart(request.user)
        else:
            # Guest Checkout
            if not session_key:
                return Response({"error": "Session key required for guest checkout"}, status=status.HTTP_400_BAD_REQUEST)
            cart = CartService.get_cart(None, session_key)
            if not cart:
                 return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # For guest, expect full address in payload
            if 'shipping_address' not in request.data:
                 return Response({"error": "shipping_address required for guest"}, status=status.HTTP_400_BAD_REQUEST)
            shipping_address_data = request.data['shipping_address']
            
            # Validate Guest Email
            if 'guest_email' not in request.data:
                 return Response({"error": "guest_email required"}, status=status.HTTP_400_BAD_REQUEST)
            request.session.save() # Ensure session is saved

        if not shipping_address_data and 'address_id' in request.data and request.user.is_authenticated:
             # Fallback if logic above skipped
             address = get_object_or_404(Address, id=request.data['address_id'], user=request.user)
             shipping_address_data = AddressSerializer(address).data

        if not shipping_address_data:
             return Response({"error": "Shipping address missing"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if not cart.items.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

            # Calculate Total & Create Order Items
            total_amount = 0
            
            # Create Order Shell
            order_data = {
                'total_amount': 0,
                'shipping_address': shipping_address_data,
                'status': Order.Status.PENDING
            }
            
            if request.user.is_authenticated:
                order_data['user'] = request.user
            else:
                order_data['guest_email'] = request.data['guest_email']
                order_data['guest_phone'] = request.data.get('guest_phone')
            
            # Payment Method
            payment_method = request.data.get('payment_method', 'ONLINE')
            order_data['payment_method'] = payment_method
            
            # If COD, we might want to set different initial status or handle limits
            # For now, default PENDING is fine.
                
            order = Order.objects.create(**order_data)

            for item in cart.items.all():
                # Lock Product for Inventory Update
                product = Product.objects.select_for_update().get(id=item.product.id)
                
                if product.stock_quantity < item.quantity:
                    raise serializers.ValidationError(
                        f"Insufficient stock for {product.name}. Available: {product.stock_quantity}"
                    )

                # Atomically decrement stock
                product.stock_quantity -= item.quantity
                product.save()

                price_info = PricingService.calculate_price(
                    item.product.id, item.length, item.breadth, item.height
                )
                unit_price = price_info['final_price']
                line_total = unit_price * item.quantity
                total_amount += line_total
                
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_snapshot={'name': item.product.name, 'code': item.product.admin_code},
                    length=item.length,
                    breadth=item.breadth,
                    height=item.height,
                    unit_price=unit_price,
                    quantity=item.quantity
                )

            order.total_amount = total_amount
            # Apply Coupon if present
            if cart.applied_promo:
                from apps.promotions.services import PromotionService
                from decimal import Decimal
                
                # Re-validate to be sure
                validation = PromotionService.validate_promo_code(
                    cart.applied_promo.code, 
                    request.user if request.user.is_authenticated else None, 
                    Decimal(str(total_amount))
                )
                
                if validation['valid']:
                    discount = validation['discount_amount']
                    total_amount = max(0, float(total_amount) - float(discount))
                    
                    # Record Usage
                    from apps.promotions.models import PromoUsage, PromoCode
                    from django.db.models import F
                    
                    PromoUsage.objects.create(
                        promo=cart.applied_promo,
                        user=request.user if request.user.is_authenticated else None,
                        order=order,
                        discount_amount=discount
                    )
                    PromoCode.objects.filter(id=cart.applied_promo.id).update(usage_count=F('usage_count') + 1)
            
            order.total_amount = total_amount
            order.save()
            
            # Clear Cart
            cart.items.all().delete()
            # Reset promo
            cart.applied_promo = None
            cart.save()
            
            # If guest, delete cart entirely
            if not request.user.is_authenticated:
                 cart.delete()
            
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class InvoiceView(APIView):
    permission_classes = [AllowAny] # Using order ID + maybe simple token/auth check? 
    # For simplicity, keeping authentication check inside or relying on URL obfuscation/UUID if public, 
    # but strictly accessing invoice usually requires auth. 
    # Let's enforce auth for users, and maybe a signed URL for guests later. 
    # For now, Authenticated or Admin. Guests? 
    # Let's require IsAuthenticated for now to start safe.
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        if order.user != request.user and request.user.role != 'ADMIN':
             return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        
        # Generate Invoice
        html_content = InvoiceService.generate_invoice_html(order)
        return HttpResponse(html_content, content_type="text/html")
