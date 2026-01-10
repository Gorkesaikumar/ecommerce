from rest_framework import serializers
from django.contrib.auth import get_user_model
from .services import OTPService
from .token_blacklist import TokenBlacklist
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class SendOTPSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=15, min_length=10)

    def validate_mobile_number(self, value):
        # Basic Validation (Add Regex in prod)
        if not value.isdigit() and not value.startswith('+'):
           raise serializers.ValidationError("Invalid mobile number format")
        return value

class VerifyOTPSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        mobile = attrs.get('mobile_number')
        otp = attrs.get('otp')

        if not OTPService.verify_otp(mobile, otp):
            raise serializers.ValidationError("Invalid or Expired OTP")
        
        return attrs

    def get_tokens(self):
        mobile = self.validated_data['mobile_number']
        
        # Get or Create User
        with transaction.atomic():
            user, created = User.objects.get_or_create(mobile_number=mobile)
        
        refresh = RefreshToken.for_user(user)
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': str(user.id),
                'mobile_number': user.mobile_number,
                'role': user.role
            }
        }

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)
    
    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs
    
    
    def save(self):
        TokenBlacklist.blacklist_token(self.token)
