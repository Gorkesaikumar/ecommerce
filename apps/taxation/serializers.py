"""
Taxation Serializers
"""
from rest_framework import serializers
from .models import TaxCategory, TaxExemption, BusinessTaxInfo


class TaxCategorySerializer(serializers.ModelSerializer):
    effective_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = TaxCategory
        fields = [
            'id', 'name', 'hsn_code', 'description',
            'cgst_rate', 'sgst_rate', 'igst_rate', 'cess_rate',
            'effective_rate'
        ]
    
    def get_effective_rate(self, obj):
        """Return total effective rate"""
        return obj.igst_rate + obj.cess_rate


class TaxCalculationRequestSerializer(serializers.Serializer):
    destination_state = serializers.CharField(max_length=50)
    
    def validate_destination_state(self, value):
        # List of valid Indian states
        valid_states = [
            'andhra pradesh', 'arunachal pradesh', 'assam', 'bihar',
            'chhattisgarh', 'goa', 'gujarat', 'haryana', 'himachal pradesh',
            'jharkhand', 'karnataka', 'kerala', 'madhya pradesh', 'maharashtra',
            'manipur', 'meghalaya', 'mizoram', 'nagaland', 'odisha', 'punjab',
            'rajasthan', 'sikkim', 'tamil nadu', 'telangana', 'tripura',
            'uttar pradesh', 'uttarakhand', 'west bengal',
            'delhi', 'chandigarh', 'puducherry', 'ladakh', 'lakshadweep',
            'andaman and nicobar islands', 'dadra and nagar haveli and daman and diu', 'jammu and kashmir'
        ]
        
        if value.lower().strip() not in valid_states:
            raise serializers.ValidationError(f"Invalid state: {value}")
        
        return value


class TaxExemptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxExemption
        fields = '__all__'


class BusinessTaxInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessTaxInfo
        fields = '__all__'
