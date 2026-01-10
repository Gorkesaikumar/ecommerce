"""
JWT Token Blacklist Service using Redis
"""
from django.core.cache import cache
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
import logging

logger = logging.getLogger(__name__)

class TokenBlacklist:
    PREFIX = "ecom:blacklist:jwt:"
    
    @staticmethod
    def _get_key(jti):
        """Generate Redis key for JWT ID"""
        return f"{TokenBlacklist.PREFIX}{jti}"
    
    @staticmethod
    def blacklist_token(token_string):
        """
        Add token to blacklist.
        TTL matches token expiry (no need to store forever)
        """
        try:
            token = RefreshToken(token_string)
            jti = str(token['jti'])
            
            # Get token expiry
            exp = token['exp']
            from datetime import datetime
            ttl = exp - int(datetime.now().timestamp())
            
            if ttl > 0:
                cache.set(TokenBlacklist._get_key(jti), "1", timeout=ttl)
                logger.info(f"Token blacklisted: {jti}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    
    @staticmethod
    def is_blacklisted(jti):
        """Check if token JTI is blacklisted"""
        return cache.get(TokenBlacklist._get_key(jti)) is not None
