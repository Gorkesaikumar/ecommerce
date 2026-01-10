"""
Shipping Calculation Service
Calculates shipping costs based on zones, rates, and order details
"""
from decimal import Decimal
from typing import Dict, List, Optional
from .models import ShippingZone, ShippingRate, ShippingMethod, PincodeServiceability
import logging

logger = logging.getLogger(__name__)


class ShippingService:
    """
    Handles all shipping-related calculations and validations.
    """
    
    # Default shipping for areas without zone configuration
    DEFAULT_SHIPPING_RATE = Decimal('99.00')
    DEFAULT_FREE_ABOVE = Decimal('1999.00')
    
    @staticmethod
    def get_zone_for_state(state: str) -> Optional[ShippingZone]:
        """
        Find shipping zone for a given state.
        """
        state_lower = state.lower().strip()
        
        zones = ShippingZone.objects.filter(is_active=True).order_by('priority')
        for zone in zones:
            if state_lower in [s.lower() for s in zone.states]:
                return zone
        
        return None
    
    @staticmethod
    def get_zone_for_pincode(pincode: str) -> Optional[ShippingZone]:
        """
        Find shipping zone for a specific pincode.
        """
        try:
            service = PincodeServiceability.objects.get(
                pincode=pincode.strip(),
                is_serviceable=True
            )
            return service.zone
        except PincodeServiceability.DoesNotExist:
            return None
    
    @staticmethod
    def check_serviceability(pincode: str) -> Dict:
        """
        Check if pincode is serviceable and get delivery options.
        """
        try:
            service = PincodeServiceability.objects.get(pincode=pincode.strip())
            
            if not service.is_serviceable:
                return {
                    'serviceable': False,
                    'message': 'Delivery not available to this pincode'
                }
            
            return {
                'serviceable': True,
                'zone': service.zone.name,
                'city': service.city,
                'state': service.state,
                'cod_available': service.cod_available,
                'prepaid_only': service.prepaid_only
            }
        except PincodeServiceability.DoesNotExist:
            # If pincode not in database, assume serviceable (fallback)
            return {
                'serviceable': True,
                'zone': 'Default',
                'city': 'Unknown',
                'state': 'Unknown',
                'cod_available': True,
                'prepaid_only': False,
                'note': 'Pincode not in database, using default zone'
            }
    
    @staticmethod
    def calculate_shipping(
        order_value: Decimal,
        destination_state: str,
        weight_kg: Decimal = Decimal('1.00'),
        shipping_method_code: str = 'STANDARD',
        pincode: str = None
    ) -> Dict:
        """
        Calculate shipping cost for an order.
        
        Args:
            order_value: Total order value (for free shipping check)
            destination_state: Destination state
            weight_kg: Total weight of order
            shipping_method_code: Shipping method (STANDARD, EXPRESS, etc.)
            pincode: Optional pincode for precise zone lookup
            
        Returns:
            Dict with shipping_cost, delivery_days, and breakdown
        """
        # Get zone
        zone = None
        if pincode:
            zone = ShippingService.get_zone_for_pincode(pincode)
        
        if not zone:
            zone = ShippingService.get_zone_for_state(destination_state)
        
        # Get shipping method
        try:
            method = ShippingMethod.objects.get(code=shipping_method_code, is_active=True)
        except ShippingMethod.DoesNotExist:
            method = None
            method_multiplier = Decimal('1.00')
            delivery_adjustment = 0
        else:
            method_multiplier = method.rate_multiplier
            delivery_adjustment = method.delivery_days_adjustment
        
        # Calculate rate
        if zone:
            # Find applicable rate
            rate = ShippingRate.objects.filter(
                zone=zone,
                is_active=True,
                min_order_value__lte=order_value
            ).filter(
                models.Q(max_order_value__gte=order_value) |
                models.Q(max_order_value__isnull=True)
            ).first()
            
            if rate:
                # Check for free shipping
                if rate.free_above and order_value >= rate.free_above:
                    shipping_cost = Decimal('0.00')
                    is_free = True
                    free_threshold = rate.free_above
                else:
                    # Calculate base + weight
                    base = rate.base_rate
                    extra_weight = max(Decimal('0.00'), weight_kg - rate.base_weight_kg)
                    weight_charge = extra_weight * rate.per_kg_rate
                    shipping_cost = (base + weight_charge) * method_multiplier
                    is_free = False
                    free_threshold = rate.free_above
                
                min_days = max(1, rate.min_delivery_days + delivery_adjustment)
                max_days = max(min_days, rate.max_delivery_days + delivery_adjustment)
                zone_name = zone.name
            else:
                # No rate found, use defaults
                shipping_cost = ShippingService.DEFAULT_SHIPPING_RATE * method_multiplier
                is_free = order_value >= ShippingService.DEFAULT_FREE_ABOVE
                if is_free:
                    shipping_cost = Decimal('0.00')
                free_threshold = ShippingService.DEFAULT_FREE_ABOVE
                min_days = 5
                max_days = 10
                zone_name = zone.name
        else:
            # No zone found, use defaults
            if order_value >= ShippingService.DEFAULT_FREE_ABOVE:
                shipping_cost = Decimal('0.00')
                is_free = True
            else:
                shipping_cost = ShippingService.DEFAULT_SHIPPING_RATE * method_multiplier
                is_free = False
            
            free_threshold = ShippingService.DEFAULT_FREE_ABOVE
            min_days = 7
            max_days = 14
            zone_name = 'Default'
        
        # Round to 2 decimal places
        shipping_cost = shipping_cost.quantize(Decimal('0.01'))
        
        return {
            'shipping_cost': shipping_cost,
            'is_free_shipping': is_free,
            'free_shipping_threshold': free_threshold,
            'amount_for_free_shipping': max(Decimal('0.00'), free_threshold - order_value) if free_threshold else None,
            'zone': zone_name,
            'shipping_method': shipping_method_code,
            'estimated_delivery': {
                'min_days': min_days,
                'max_days': max_days,
                'display': f"{min_days}-{max_days} business days"
            },
            'weight_kg': str(weight_kg)
        }
    
    @staticmethod
    def get_available_methods(destination_state: str = None) -> List[Dict]:
        """
        Get all available shipping methods with estimated rates.
        """
        methods = ShippingMethod.objects.filter(is_active=True).order_by('priority')
        
        return [
            {
                'code': m.code,
                'name': m.name,
                'description': m.description,
                'rate_multiplier': str(m.rate_multiplier),
                'has_tracking': m.has_tracking,
                'delivery_adjustment': m.delivery_days_adjustment
            }
            for m in methods
        ]
    
    @staticmethod
    def estimate_for_cart(cart, destination_state: str, pincode: str = None) -> Dict:
        """
        Estimate shipping for a cart.
        """
        from apps.products.services import PricingService
        
        total_value = Decimal('0.00')
        total_weight = Decimal('0.00')  # Would need weight on products
        
        for item in cart.items.all():
            try:
                price_info = PricingService.calculate_price(
                    item.product, item.length, item.breadth, item.height
                )
                total_value += price_info['final_price'] * item.quantity
            except Exception:
                total_value += item.product.base_price * item.quantity
            
            # Estimate weight (would need actual weight field)
            total_weight += Decimal('0.5') * item.quantity
        
        return ShippingService.calculate_shipping(
            order_value=total_value,
            destination_state=destination_state,
            weight_kg=total_weight,
            pincode=pincode
        )


# Import models for Q object
from django.db import models
