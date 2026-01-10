"""
Custom JWT Authentication with Blacklist Enforcement

This authentication backend extends SimpleJWT to check if tokens have been
revoked via the Redis-based blacklist. This ensures that:
1. Logout actually invalidates tokens
2. Admin force-logout works
3. Compromised tokens can be revoked immediately
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from .token_blacklist import TokenBlacklist
import logging

logger = logging.getLogger(__name__)


class BlacklistCheckingJWTAuthentication(JWTAuthentication):
    """
    Extends SimpleJWT to check if tokens have been revoked.
    
    On every authenticated request:
    1. Validates token signature and expiry (parent class)
    2. Checks if JTI is in Redis blacklist
    3. Rejects if blacklisted
    """
    
    def get_validated_token(self, raw_token):
        """
        Override to add blacklist check after standard validation.
        """
        validated_token = super().get_validated_token(raw_token)
        jti = validated_token.get('jti')
        
        if jti and TokenBlacklist.is_blacklisted(jti):
            logger.warning(f"Rejected blacklisted token: {jti[:8]}...")
            raise InvalidToken('Token has been revoked')
        
        return validated_token
