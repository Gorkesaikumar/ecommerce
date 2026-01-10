"""
Promotions Service
Handles validation and calculation of discounts
"""
from decimal import Decimal
from django.utils import timezone
from .models import PromoCode, PromoUsage
from django.db.models import F
import logging

logger = logging.getLogger(__name__)

class PromotionService:
    
    @staticmethod
    def validate_promo_code(code: str, user=None, order_total: Decimal = Decimal('0.00')) -> dict:
        """
        Validate a promo code for applicability.
        """
        try:
            promo = PromoCode.objects.get(code__iexact=code)
        except PromoCode.DoesNotExist:
            return {'valid': False, 'message': 'Invalid promo code'}
        
        is_valid, msg = promo.is_valid()
        if not is_valid:
            return {'valid': False, 'message': msg}
            
        if order_total < promo.min_order_amount:
            return {'valid': False, 'message': f'Minimum order amount of {promo.min_order_amount} required'}
            
        if user and user.is_authenticated:
            user_usage = PromoUsage.objects.filter(promo=promo, user=user).count()
            if user_usage >= promo.per_user_limit:
                return {'valid': False, 'message': 'You have already used this promo code'}
        
        # Calculate estimated discount
        discount_amount = PromotionService.calculate_discount(promo, order_total)
        
        return {
            'valid': True,
            'promo': promo,
            'discount_amount': discount_amount,
            'message': 'Promo code applied successfully'
        }

    @staticmethod
    def calculate_discount(promo: PromoCode, order_total: Decimal) -> Decimal:
        if promo.discount_type == 'FIXED':
            discount = promo.discount_value
        else:
            discount = order_total * (promo.discount_value / Decimal('100.00'))
            if promo.max_discount_amount:
                discount = min(discount, promo.max_discount_amount)
        
        # Ensure discount doesn't exceed total
        return min(discount, order_total)

    @staticmethod
    def apply_promo_to_order(order, code: str):
        """
        Apply promo to an order being created/updated.
        Should be called inside a transaction.
        """
        validation = PromotionService.validate_promo_code(code, order.user, order.total_amount)
        if not validation['valid']:
            raise ValueError(validation['message'])
            
        promo = validation['promo']
        discount = validation['discount_amount']
        
        # Record usage
        PromoUsage.objects.create(
            promo=promo,
            user=order.user,
            order=order,
            discount_amount=discount
        )
        
        # Increment global counter
        PromoCode.objects.filter(id=promo.id).update(usage_count=F('usage_count') + 1)
        
        return discount
