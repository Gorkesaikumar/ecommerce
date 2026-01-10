import random
import hashlib
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class OTPService:
    @staticmethod
    def get_otp_key(mobile_number: str) -> str:
        return f"ecom:auth:otp:{mobile_number}"

    @staticmethod
    def get_rate_limit_key(mobile_number: str) -> str:
        return f"ecom:auth:limit:{mobile_number}"

    @staticmethod
    def _hash_otp(otp: str) -> str:
        return hashlib.sha256(otp.encode()).hexdigest()

    @staticmethod
    def generate_otp(mobile_number: str) -> str:
        """
        Generates a 6-digit OTP, HASHES it, and stores in Redis with 5 min expiry.
        Strict 3 requests per 10 mins rate limit.
        """
        rate_key = OTPService.get_rate_limit_key(mobile_number)
        attempts = cache.get(rate_key, 0)
        
        if attempts >= 3:
            logger.warning(f"OTP Rate Limit Reached for {mobile_number}")
            raise Exception("Too many OTP requests. Please wait 10 minutes.")
        
        otp = str(random.randint(100000, 999999))
        hashed_otp = OTPService._hash_otp(otp)
        
        # Store Hashed OTP
        cache_key = OTPService.get_otp_key(mobile_number)
        cache.set(cache_key, hashed_otp, timeout=300) # 5 minutes
        
        # Increment Rate Limit
        # Determine TTL for rate limit (reset if new)
        if attempts == 0:
            cache.set(rate_key, 1, timeout=600)  # 10 minutes window start
        else:
            cache.incr(rate_key)

        # OTP should be sent via SMS gateway in production
        # For development, check Redis directly or use test mode
        logger.info(f"OTP generated for {mobile_number}: {otp}")
        return otp

    @staticmethod
    def verify_otp(mobile_number: str, otp: str) -> bool:
        cache_key = OTPService.get_otp_key(mobile_number)
        stored_hash = cache.get(cache_key)
        
        if not stored_hash:
            return False
            
        hashed_input = OTPService._hash_otp(otp)
        
        if stored_hash == hashed_input:
            cache.delete(cache_key) # Single use
            # Clear rate limit on success? Optional. Keeping it prevents spam.
            return True
        return False
