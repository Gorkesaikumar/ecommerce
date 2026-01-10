"""
Tax Calculation Service
Handles GST calculation for orders with intra/inter-state logic
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List
from django.conf import settings
from .models import TaxCategory, BusinessTaxInfo
import logging

logger = logging.getLogger(__name__)


# Default tax category for products without explicit mapping
DEFAULT_GST_RATE = Decimal('18.00')

# Business state (source of supply)
BUSINESS_STATE = "Telangana"


class TaxCalculationService:
    """
    Calculates GST taxes for orders based on source and destination states.
    
    Rules:
    - Intra-state (same state): CGST + SGST
    - Inter-state (different states): IGST
    """
    
    @staticmethod
    def get_business_state() -> str:
        """Get the registered business state"""
        try:
            business = BusinessTaxInfo.objects.first()
            return business.state_name if business else BUSINESS_STATE
        except Exception:
            return BUSINESS_STATE
    
    @staticmethod
    def is_intra_state(destination_state: str) -> bool:
        """Check if transaction is intra-state"""
        business_state = TaxCalculationService.get_business_state()
        return destination_state.lower().strip() == business_state.lower().strip()
    
    @staticmethod
    def get_tax_category_for_product(product) -> TaxCategory:
        """
        Get tax category for a product.
        Falls back to default rates if not configured.
        """
        # Check if product's category has a linked tax category
        if hasattr(product, 'category') and product.category:
            if hasattr(product.category, 'tax_category') and product.category.tax_category:
                return product.category.tax_category
        
        # Fallback: Get or create a default category
        default_category, _ = TaxCategory.objects.get_or_create(
            name="Default (18%)",
            defaults={
                'hsn_code': '9999',
                'cgst_rate': Decimal('9.00'),
                'sgst_rate': Decimal('9.00'),
                'igst_rate': Decimal('18.00'),
            }
        )
        return default_category
    
    @staticmethod
    def calculate_item_tax(
        item_amount: Decimal,
        tax_category: TaxCategory,
        destination_state: str
    ) -> Dict:
        """
        Calculate tax for a single item.
        
        Args:
            item_amount: Taxable amount (price * quantity)
            tax_category: TaxCategory instance
            destination_state: Delivery state
            
        Returns:
            Dict with cgst, sgst, igst, cess, total_tax, and net_amount
        """
        is_intra = TaxCalculationService.is_intra_state(destination_state)
        rates = tax_category.get_effective_rate(is_intra)
        
        # Calculate individual tax components
        cgst_amount = (item_amount * rates['cgst'] / 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        sgst_amount = (item_amount * rates['sgst'] / 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        igst_amount = (item_amount * rates['igst'] / 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        cess_amount = (item_amount * rates['cess'] / 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        total_tax = cgst_amount + sgst_amount + igst_amount + cess_amount
        
        return {
            'taxable_amount': item_amount,
            'cgst_rate': rates['cgst'],
            'cgst_amount': cgst_amount,
            'sgst_rate': rates['sgst'],
            'sgst_amount': sgst_amount,
            'igst_rate': rates['igst'],
            'igst_amount': igst_amount,
            'cess_rate': rates['cess'],
            'cess_amount': cess_amount,
            'total_tax': total_tax,
            'net_amount': item_amount + total_tax,
            'hsn_code': tax_category.hsn_code,
            'is_intra_state': is_intra
        }
    
    @staticmethod
    def calculate_order_tax(order, destination_state: str = None) -> Dict:
        """
        Calculate taxes for an entire order.
        
        Args:
            order: Order instance with items
            destination_state: Override for destination (defaults to order address)
            
        Returns:
            Dict with item-wise taxes and order totals
        """
        # Get destination state from order if not provided
        if not destination_state:
            if hasattr(order, 'shipping_address') and order.shipping_address:
                destination_state = order.shipping_address.get('state', BUSINESS_STATE)
            else:
                destination_state = BUSINESS_STATE
        
        item_taxes = []
        total_cgst = Decimal('0.00')
        total_sgst = Decimal('0.00')
        total_igst = Decimal('0.00')
        total_cess = Decimal('0.00')
        total_taxable = Decimal('0.00')
        total_tax = Decimal('0.00')
        
        # Calculate tax for each item
        for item in order.items.all():
            # Get tax category for this product
            tax_category = TaxCalculationService.get_tax_category_for_product(item.product)
            
            # Calculate taxable amount
            item_amount = item.unit_price * item.quantity
            
            # Calculate tax
            tax_info = TaxCalculationService.calculate_item_tax(
                item_amount, tax_category, destination_state
            )
            
            # Add item identification
            tax_info['item_id'] = str(item.id)
            tax_info['product_name'] = item.product.name if item.product else 'Unknown'
            tax_info['quantity'] = item.quantity
            
            item_taxes.append(tax_info)
            
            # Accumulate totals
            total_cgst += tax_info['cgst_amount']
            total_sgst += tax_info['sgst_amount']
            total_igst += tax_info['igst_amount']
            total_cess += tax_info['cess_amount']
            total_taxable += item_amount
            total_tax += tax_info['total_tax']
        
        return {
            'order_id': str(order.id),
            'destination_state': destination_state,
            'is_intra_state': TaxCalculationService.is_intra_state(destination_state),
            'items': item_taxes,
            'summary': {
                'total_taxable_amount': total_taxable,
                'total_cgst': total_cgst,
                'total_sgst': total_sgst,
                'total_igst': total_igst,
                'total_cess': total_cess,
                'total_tax': total_tax,
                'grand_total': total_taxable + total_tax
            }
        }
    
    @staticmethod
    def calculate_cart_tax(cart, destination_state: str) -> Dict:
        """
        Calculate taxes for a cart (before order creation).
        Used for showing tax breakdown in checkout.
        """
        from apps.products.services import PricingService
        
        item_taxes = []
        total_cgst = Decimal('0.00')
        total_sgst = Decimal('0.00')
        total_igst = Decimal('0.00')
        total_cess = Decimal('0.00')
        total_taxable = Decimal('0.00')
        total_tax = Decimal('0.00')
        
        for item in cart.items.all():
            # Calculate item price using dimension pricing
            try:
                price_info = PricingService.calculate_price(
                    item.product, item.length, item.breadth, item.height
                )
                item_amount = price_info['final_price'] * item.quantity
            except Exception:
                item_amount = item.product.base_price * item.quantity
            
            # Get tax category
            tax_category = TaxCalculationService.get_tax_category_for_product(item.product)
            
            # Calculate tax
            tax_info = TaxCalculationService.calculate_item_tax(
                item_amount, tax_category, destination_state
            )
            tax_info['product_name'] = item.product.name
            tax_info['quantity'] = item.quantity
            
            item_taxes.append(tax_info)
            
            total_cgst += tax_info['cgst_amount']
            total_sgst += tax_info['sgst_amount']
            total_igst += tax_info['igst_amount']
            total_cess += tax_info['cess_amount']
            total_taxable += item_amount
            total_tax += tax_info['total_tax']
        
        return {
            'destination_state': destination_state,
            'is_intra_state': TaxCalculationService.is_intra_state(destination_state),
            'items': item_taxes,
            'summary': {
                'total_taxable_amount': total_taxable,
                'total_cgst': total_cgst,
                'total_sgst': total_sgst,
                'total_igst': total_igst,
                'total_cess': total_cess,
                'total_tax': total_tax,
                'grand_total': total_taxable + total_tax
            }
        }
