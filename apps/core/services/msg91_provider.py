"""
MSG91 SMS Provider Implementation

Official MSG91 API Documentation: https://docs.msg91.com/
"""
import requests
from typing import Dict, Optional
from django.conf import settings
import logging

from .sms_service import SMSService

logger = logging.getLogger(__name__)


class MSG91Provider(SMSService):
    """
    MSG91 implementation of SMS service.
    
    Supports:
    - OTP API (v5)
    - SMS API (v5) for transactional messages
    """
    
    def __init__(self):
        self.auth_key = getattr(settings, 'MSG91_AUTH_KEY', '')
        self.sender_id = getattr(settings, 'MSG91_SENDER_ID', 'ECOMM')
        self.base_url = "https://control.msg91.com/api/v5"
        self.enabled = getattr(settings, 'SMS_ENABLED', False)
        
        if not self.enabled:
            logger.warning("SMS is disabled. Set SMS_ENABLED=True in settings to enable.")
    
    def send_otp(self, mobile_number: str, otp: str, template_id: Optional[str] = None) -> Dict:
        """
        Send OTP using MSG91 OTP API.
        
        MSG91 OTP API v5 endpoint: POST /otp
        """
        if not self._validate_mobile(mobile_number):
            return {'success': False, 'message': 'Invalid mobile number format', 'provider_response': {}}
        
        if not self.enabled or not self.auth_key:
            # Development mode: log to console
            msg = f"========================================\n[DEV MODE] OTP for {mobile_number}: {otp}\n========================================"
            logger.info(msg)
            print(msg)  # Force print to ensure user sees it
            return {
                'success': True, 
                'message': 'OTP logged (dev mode)', 
                'provider_response': {'mode': 'dev'}
            }
        
        url = f"{self.base_url}/otp"
        
        # Clean mobile number (MSG91 expects format: 91XXXXXXXXXX)
        clean_mobile = mobile_number.replace('+', '').replace(' ', '').replace('-', '')
        
        payload = {
            "template_id": template_id or getattr(settings, 'MSG91_OTP_TEMPLATE_ID', ''),
            "mobile": clean_mobile,
            "otp": otp
        }
        
        headers = {
            "authkey": self.auth_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('type') == 'success':
                self._log_delivery(mobile_number, {'success': True, 'message': 'OTP sent'}, 'OTP')
                return {
                    'success': True,
                    'message': 'OTP sent successfully',
                    'provider_response': response_data
                }
            else:
                error_msg = response_data.get('message', 'Unknown error')
                self._log_delivery(mobile_number, {'success': False, 'message': error_msg}, 'OTP')
                return {
                    'success': False,
                    'message': f'MSG91 Error: {error_msg}',
                    'provider_response': response_data
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"MSG91 OTP API timeout for {mobile_number}")
            return {'success': False, 'message': 'SMS gateway timeout', 'provider_response': {}}
        except requests.exceptions.RequestException as e:
            logger.error(f"MSG91 OTP API error for {mobile_number}: {e}")
            return {'success': False, 'message': str(e), 'provider_response': {}}
    
    def send_transactional(
        self, 
        mobile_number: str, 
        message: str, 
        template_id: Optional[str] = None,
        variables: Optional[Dict] = None
    ) -> Dict:
        """
        Send transactional SMS using MSG91 SMS API.
        
        MSG91 SMS API v5 endpoint: POST /flow
        """
        if not self._validate_mobile(mobile_number):
            return {'success': False, 'message': 'Invalid mobile number format', 'provider_response': {}}
        
        if not self.enabled or not self.auth_key:
            # Development mode
            logger.info(f"[DEV MODE] Transactional SMS to {mobile_number}: {message}")
            return {
                'success': True, 
                'message': 'SMS logged (dev mode)', 
                'provider_response': {'mode': 'dev'}
            }
        
        url = f"{self.base_url}/flow"
        
        clean_mobile = mobile_number.replace('+', '').replace(' ', '').replace('-', '')
        
        payload = {
            "sender": self.sender_id,
            "mobiles": clean_mobile,
        }
        
        # If template_id is provided, use template-based sending
        if template_id:
            payload["template_id"] = template_id
            if variables:
                payload["VAR1"] = variables.get('var1', '')
                payload["VAR2"] = variables.get('var2', '')
                # Add more variables as needed
        else:
            # Direct message sending (requires DLT approval)
            payload["message"] = message
        
        headers = {
            "authkey": self.auth_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('type') == 'success':
                self._log_delivery(mobile_number, {'success': True, 'message': 'SMS sent'}, 'TRANSACTIONAL')
                return {
                    'success': True,
                    'message': 'SMS sent successfully',
                    'provider_response': response_data
                }
            else:
                error_msg = response_data.get('message', 'Unknown error')
                self._log_delivery(mobile_number, {'success': False, 'message': error_msg}, 'TRANSACTIONAL')
                return {
                    'success': False,
                    'message': f'MSG91 Error: {error_msg}',
                    'provider_response': response_data
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"MSG91 SMS API timeout for {mobile_number}")
            return {'success': False, 'message': 'SMS gateway timeout', 'provider_response': {}}
        except requests.exceptions.RequestException as e:
            logger.error(f"MSG91 SMS API error for {mobile_number}: {e}")
            return {'success': False, 'message': str(e), 'provider_response': {}}
    
    def send_promotional(self, mobile_number: str, message: str) -> Dict:
        """
        Send promotional SMS.
        Note: Requires DLT registration and promotional sender ID.
        """
        # Promotional SMS uses same endpoint as transactional but with different sender ID
        # For now, delegate to transactional
        return self.send_transactional(mobile_number, message)


# Factory function to get SMS service instance
def get_sms_service() -> SMSService:
    """
    Factory function to get configured SMS service provider.
    
    Returns instance based on SMS_PROVIDER setting.
    Currently only MSG91 is implemented.
    """
    provider = getattr(settings, 'SMS_PROVIDER', 'MSG91')
    
    if provider == 'MSG91':
        return MSG91Provider()
    else:
        raise ValueError(f"Unsupported SMS provider: {provider}")
