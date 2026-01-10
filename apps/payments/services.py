import razorpay
from django.conf import settings
from rest_framework.exceptions import ValidationError

class RazorpayService:
    @staticmethod
    def get_client():
        # Using environment variables for keys. 
        # Ensure RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are in .env
        return razorpay.Client(auth=(
            settings.RAZORPAY_KEY_ID, 
            settings.RAZORPAY_KEY_SECRET
        ))

    @staticmethod
    def create_order(amount_in_inr: float, receipt: str) -> dict:
        client = RazorpayService.get_client()
        data = {
            "amount": int(amount_in_inr * 100), # Convert to paise
            "currency": "INR",
            "receipt": str(receipt),
            "payment_capture": 1 
        }
        order = client.order.create(data=data)
        return order

    @staticmethod
    def verify_signature(data: dict) -> bool:
        client = RazorpayService.get_client()
        try:
            client.utility.verify_payment_signature(data)
            return True
        except razorpay.errors.SignatureVerificationError:
            return False
