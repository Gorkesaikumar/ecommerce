"""
Taxation Models - GST/Tax Calculation Engine
Supports CGST+SGST (intra-state) and IGST (inter-state) calculations
"""
from django.db import models
from decimal import Decimal
import uuid


class TaxCategory(models.Model):
    """
    Tax categories mapped to HSN codes for GST compliance.
    Each product category maps to a tax category.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    hsn_code = models.CharField(max_length=10, help_text="Harmonized System Nomenclature code")
    description = models.TextField(blank=True)
    
    # GST Rates
    cgst_rate = models.DecimalField(
        max_digits=5, decimal_places=2, 
        help_text="Central GST rate (e.g., 9.00 for 9%)"
    )
    sgst_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="State GST rate (e.g., 9.00 for 9%)"
    )
    igst_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Integrated GST rate (e.g., 18.00 for 18%)"
    )
    
    # Cess (for luxury items)
    cess_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        help_text="Additional cess if applicable"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Tax Categories"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.hsn_code}) - {self.igst_rate}%"
    
    def get_effective_rate(self, is_intra_state: bool) -> dict:
        """Get applicable tax rates based on transaction type"""
        if is_intra_state:
            return {
                'cgst': self.cgst_rate,
                'sgst': self.sgst_rate,
                'igst': Decimal('0.00'),
                'cess': self.cess_rate,
                'total': self.cgst_rate + self.sgst_rate + self.cess_rate
            }
        else:
            return {
                'cgst': Decimal('0.00'),
                'sgst': Decimal('0.00'),
                'igst': self.igst_rate,
                'cess': self.cess_rate,
                'total': self.igst_rate + self.cess_rate
            }


class TaxExemption(models.Model):
    """
    Tax exemptions for specific scenarios
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    exemption_type = models.CharField(
        max_length=20,
        choices=[
            ('FULL', 'Full Exemption'),
            ('PARTIAL', 'Partial Exemption'),
            ('CATEGORY', 'Category-Based'),
        ]
    )
    exemption_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('100.00')
    )
    applicable_states = models.JSONField(
        default=list, 
        help_text="List of states where exemption applies"
    )
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.exemption_percentage}%"


class BusinessTaxInfo(models.Model):
    """
    Business registration details for tax compliance
    """
    gstin = models.CharField(
        max_length=15, unique=True,
        help_text="15-digit GSTIN"
    )
    legal_name = models.CharField(max_length=255)
    trade_name = models.CharField(max_length=255)
    registered_address = models.TextField()
    state_code = models.CharField(max_length=2)
    state_name = models.CharField(max_length=50, default="Telangana")
    pan = models.CharField(max_length=10)
    is_composition_dealer = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Business Tax Info"
        verbose_name_plural = "Business Tax Info"
    
    def __str__(self):
        return f"{self.trade_name} - {self.gstin}"
