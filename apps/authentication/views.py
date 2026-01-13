from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import SendOTPSerializer, VerifyOTPSerializer, LogoutSerializer
from .services import OTPService
import logging

logger = logging.getLogger(__name__)

from rest_framework.throttling import ScopedRateThrottle

class SendOTPView(APIView):
    authentication_classes = []  # Disable auth checks to prevent 401 on stale cookies
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
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
    authentication_classes = []  # Disable auth checks
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            tokens = serializer.get_tokens()
            
            # Hybrid App: Set JWT Cookie for Template Views (Middleware handled)
            # We NO LONGER use django.contrib.auth.login() to avoid destroying Admin sessions.
            # Isolation Strategy: Customer = JWT Cookie, Admin = Session Cookie.
            
            response = Response(tokens, status=status.HTTP_200_OK)
            
            # Set Secure HTTPOnly Cookie
            response.set_cookie(
                'access_token', 
                tokens['access'], 
                httponly=True, 
                samesite='Lax',
                max_age=30 * 24 * 60 * 60 # 30 Days (matches access token lifetime config)
            )
            
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
