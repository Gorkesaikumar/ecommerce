from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .profile_serializers import UserProfileSerializer, AdminUserUpdateSerializer, ChangePasswordSerializer
from apps.core.models import AuditLog
import logging

logger = logging.getLogger(__name__)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """User can view and update their own profile"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        return self.request.user
    
    def perform_update(self, serializer):
        serializer.save()
        logger.info(f"User {self.request.user.email} updated profile. IP: {self._get_client_ip(self.request)}")

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Log password change
            logger.info(f"User changed password: {user.email}")
            
            return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminUserUpdateView(APIView):
    """
    Admin user management:
    - POST: Change Role (Legacy support, though ideally PATCH)
    - PATCH: Update Details (Name, Email, Mobile, Role)
    - DELETE: Delete User (Protected)
    """
    permission_classes = [IsAuthenticated]
    
    def _get_target_user(self, user_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    def post(self, request, user_id):
        # Legacy Role update support
        return self.patch(request, user_id)

    def patch(self, request, user_id):
        if request.user.role != 'ADMIN':
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        
        target_user = self._get_target_user(user_id)
        if not target_user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # Prevent editing other Admins if needed, or allow superadmin?
        # For now, allow editing, but careful with Role
        
        # We can reuse a serializer or update manually for flexibility here
        # Using AdminUserUpdateSerializer for role, but might need broader one.
        # Let's handle manually for now to support name/email updates quickly
        
        data = request.data
        changes = {}
        
        if 'name' in data:
            target_user.name = data['name']
            changes['name'] = data['name']
        if 'email' in data:
            target_user.email = data['email']
            changes['email'] = data['email']
        if 'mobile_number' in data:
            target_user.mobile_number = data['mobile_number']
            changes['mobile_number'] = data['mobile_number']
            
        if 'role' in data:
            old_role = target_user.role
            new_role = data['role']
            target_user.role = new_role
            changes['role'] = {'old': old_role, 'new': new_role}

        try:
            target_user.save()
        except Exception as e:
            # Handle unique constraints etc
            if 'unique constraint' in str(e).lower():
                return Response({'error': 'Email or Mobile Number already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Audit log
        AuditLog.objects.create(
            user=request.user,
            user_mobile=request.user.mobile_number,
            user_role=request.user.role,
            action='USER_UPDATE',
            resource_type='User',
            resource_id=str(target_user.id),
            changes=changes,
            reason=data.get('reason', 'Admin Update'),
            ip_address=self._get_client_ip(request)
        )
        
        return Response({'message': 'User updated successfully'})

    def delete(self, request, user_id):
        if request.user.role != 'ADMIN':
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
            
        target_user = self._get_target_user(user_id)
        if not target_user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # PROTECTION: Cannot delete Admin
        if target_user.role == 'ADMIN':
            return Response({'error': 'Cannot delete an Administrator account.'}, status=status.HTTP_403_FORBIDDEN)
            
        # Proceed with deletion
        # This will cascade delete orders usually, or set null depending on models.
        # Assuming cascade is desired based on user request "customers data his orders should be deleted"
        
        user_id_str = str(target_user.id)
        target_user.delete()
        
        AuditLog.objects.create(
            user=request.user,
            user_mobile=request.user.mobile_number,
            user_role=request.user.role,
            action='USER_DELETE',
            resource_type='User',
            resource_id=user_id_str,
            changes={},
            reason='Admin Deletion',
            ip_address=self._get_client_ip(request)
        )
        
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
