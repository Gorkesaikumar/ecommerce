from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'mobile_number', 'name', 'email', 'role', 'profile_photo', 'date_joined']
        read_only_fields = ['id', 'mobile_number', 'role', 'date_joined']
    
    def validate_name(self, value):
        if len(value) > 255:
            raise serializers.ValidationError("Name too long")
        return value

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords do not match")
        return data

class AdminUserUpdateSerializer(serializers.Serializer):
    """Admin can update user role"""
    role = serializers.ChoiceField(choices=User.Roles.choices)
    reason = serializers.CharField(max_length=500, required=True)
