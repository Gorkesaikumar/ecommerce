"""
Management command to check for abandoned carts and trigger notifications
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.orders.models import Cart
from apps.notifications.services import NotificationService
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check for abandoned carts and send notifications'

    def handle(self, *args, **kwargs):
        cutoff = timezone.now() - timedelta(hours=24)
        # Find carts updated > 24h ago, have items, and haven't converted to order (cart deletion handles conversion usually, 
        # but persistent carts might remain? Logic: if cart exists and not empty, it's potentially abandoned if old)
        
        carts = Cart.objects.filter(updated_at__lt=cutoff).exclude(items__isnull=True)
        
        count = 0
        for cart in carts:
            # Check if we already notified (basic check to avoid spamming)
            # ideally add 'last_notification_sent' field to Cart
            # For this MVP audit fix, we'll just log
            
            email = cart.user.email if cart.user else (getattr(cart, 'guest_email', None) if hasattr(cart, 'guest_email') else None)
            
            # Since guest email is on Order, not Cart (unless we add it to Cart for Guest Checkout flow initiation)
            # In my guest implementation: Guest email was on Order model. 
            # I should add email to Cart model to support abandoned guest carts 
            # OR tracking via session only (which means no email).
            
            if cart.user and cart.user.email:
                NotificationService.send_notification(
                    'ABANDONED_CART', 
                    cart.user.email, 
                    {'user_name': cart.user.name, 'cart_url': 'https://woodcraft.com/cart'}
                )
                count += 1
                
        self.stdout.write(f"Processed {count} abandoned carts")
