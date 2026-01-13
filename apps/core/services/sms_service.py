"""
Abstract SMS Service Base Class

Provides a provider-agnostic interface for SMS delivery.
Implementations can use MSG91, Twilio, AWS SNS, or any other provider.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SMSService(ABC):
    """
    Abstract base class for SMS service providers.
    """
    
    @abstractmethod
    def send_otp(self, mobile_number: str, otp: str, template_id: Optional[str] = None) -> Dict:
        """
        Send OTP via SMS.
        
        Args:
            mobile_number: Recipient mobile number (with country code)
            otp: The OTP code to send
            template_id: Optional template ID for the provider
            
        Returns:
            Dict with keys: success (bool), message (str), provider_response (dict)
        """
        pass
    
    @abstractmethod
    def send_transactional(
        self, 
        mobile_number: str, 
        message: str, 
        template_id: Optional[str] = None,
        variables: Optional[Dict] = None
    ) -> Dict:
        """
        Send transactional SMS (order confirmations, updates).
        
        Args:
            mobile_number: Recipient mobile number
            message: SMS content
            template_id: Optional template ID
            variables: Optional dict of template variables
            
        Returns:
            Dict with keys: success (bool), message (str), provider_response (dict)
        """
        pass
    
    @abstractmethod
    def send_promotional(self, mobile_number: str, message: str) -> Dict:
        """
        Send promotional SMS (marketing, offers).
        
        Args:
            mobile_number: Recipient mobile number
            message: SMS content
            
        Returns:
            Dict with keys: success (bool), message (str), provider_response (dict)
        """
        pass
    
    def _validate_mobile(self, mobile_number: str) -> bool:
        """
        Validate mobile number format.
        """
        # Basic validation: should start with + and have 10-15 digits
        if not mobile_number.startswith('+'):
            return False
        
        digits = mobile_number[1:].replace(' ', '').replace('-', '')
        return digits.isdigit() and 10 <= len(digits) <= 15
    
    def _log_delivery(self, mobile_number: str, result: Dict, sms_type: str):
        """
        Log SMS delivery attempt.
        """
        status = "SUCCESS" if result.get('success') else "FAILED"
        logger.info(f"SMS {sms_type} to {mobile_number}: {status} - {result.get('message')}")
