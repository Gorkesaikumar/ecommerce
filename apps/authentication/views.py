from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import SendOTPSerializer, VerifyOTPSerializer, LogoutSerializer
from .services import OTPService
import logging

logger = logging.getLogger(__name__)

class SendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = 'otp'

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            mobile = serializer.validated_data['mobile_number']
            try:
                OTPService.generate_otp(mobile) 
                # Generic response - prevents account enumeration
                return Response(
                    {"message": "If this number is registered, an OTP has been sent."}, 
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                logger.error(f"OTP Error: {e}")
                return Response({"error": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            tokens = serializer.get_tokens()
            
            # Hybrid App: Log user in for Session Auth (Templates)
            from django.contrib.auth import login, get_user_model
            User = get_user_model()
            mobile = serializer.validated_data['mobile_number']
            user = User.objects.get(mobile_number=mobile)
            login(request, user)
            
            return Response(tokens, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
