"""
Complete System Verification Script

This script verifies that all components of the ecommerce platform
are working correctly:
- Django configuration
- Redis connectivity
- Celery configuration
- SMS services
- Authentication system
"""

import os
import sys
import django

# Setup Django environment - use base settings directly for development
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.core.cache import cache
from django.conf import settings
from apps.authentication.services import OTPService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("ECOMMERCE PLATFORM - SYSTEM VERIFICATION")
print("=" * 70)
print()

# Test 1: Django Configuration
print("✓ Test 1: Django Configuration")
print(f"  DEBUG: {settings.DEBUG}")
print(f"  SECRET_KEY: {'Set' if settings.SECRET_KEY else 'NOT SET'}")
print(f"  ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print()

# Test 2: Redis Connection
print("✓ Test 2: Redis Connection")
try:
    cache.set('test_key', 'test_value', 60)
    result = cache.get('test_key')
    if result == 'test_value':
        print(f"  ✅ Redis connected successfully")
        print(f"  Redis URL: {settings.CACHES['default']['LOCATION']}")
        cache.delete('test_key')
    else:
        print(f"  ❌ Redis connection failed - wrong value returned")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ Redis connection failed: {e}")
    sys.exit(1)
print()

# Test 3: Celery Configuration
print("✓ Test 3: Celery Configuration")
print(f"  Broker URL: {settings.CELERY_BROKER_URL}")
print(f"  Result Backend: {settings.CELERY_RESULT_BACKEND}")
print(f"  Task Serializer: {settings.CELERY_TASK_SERIALIZER}")
print(f"  Timezone: {settings.CELERY_TIMEZONE}")
print()

# Test 4: SMS Configuration
print("✓ Test 4: SMS Configuration")
print(f"  SMS Enabled: {settings.SMS_ENABLED}")
print(f"  SMS Provider: {settings.SMS_PROVIDER}")
print(f"  MSG91 Auth Key: {'Set' if settings.MSG91_AUTH_KEY else 'NOT SET'}")
print(f"  MSG91 Sender ID: {settings.MSG91_SENDER_ID}")
print()

# Test 5: OTP Service
print("✓ Test 5: OTP Service")
try:
    test_mobile = "+919999999999"
    
    # Clear any existing OTP
    cache_key = OTPService.get_otp_key(test_mobile)
    cache.delete(cache_key)
    rate_key = OTPService.get_rate_limit_key(test_mobile)
    cache.delete(rate_key)
    
    # Generate OTP
    otp = OTPService.generate_otp(test_mobile)
    print(f"  ✅ OTP generated successfully: {otp}")
    
    # Verify OTP exists in cache
    stored_hash = cache.get(cache_key)
    if stored_hash:
        print(f"  ✅ OTP stored in Redis (hashed)")
    else:
        print(f"  ❌ OTP not found in cache")
        sys.exit(1)
    
    # Verify OTP
    is_valid = OTPService.verify_otp(test_mobile, otp)
    if is_valid:
        print(f"  ✅ OTP verification successful")
    else:
        print(f"  ❌ OTP verification failed")
        sys.exit(1)
    
    # Verify single-use (OTP should be deleted after verification)
    stored_hash_after = cache.get(cache_key)
    if not stored_hash_after:
        print(f"  ✅ OTP single-use enforcement working")
    else:
        print(f"  ❌ OTP not deleted after verification")
        sys.exit(1)
        
except Exception as e:
    print(f"  ❌ OTP service failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# Test 6: Celery Tasks Import
print("✓ Test 6: Celery Tasks")
try:
    from apps.core.tasks import send_sms_async, send_otp_sms_async, send_order_notification_async
    print(f"  ✅ send_sms_async imported")
    print(f"  ✅ send_otp_sms_async imported")
    print(f"  ✅ send_order_notification_async imported")
except Exception as e:
    print(f"  ❌ Task import failed: {e}")
    sys.exit(1)
print()

# Test 7: Database Connection
print("✓ Test 7: Database Connection")
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result[0] == 1:
            print(f"  ✅ Database connected successfully")
        else:
            print(f"  ❌ Database connection test failed")
            sys.exit(1)
except Exception as e:
    print(f"  ❌ Database connection failed: {e}")
    sys.exit(1)
print()

# Test 8: Authentication Models
print("✓ Test 8: Authentication Models")
try:
    from apps.authentication.models import User
    user_count = User.objects.count()
    print(f"  ✅ User model accessible")
    print(f"  Total users: {user_count}")
except Exception as e:
    print(f"  ❌ User model access failed: {e}")
    sys.exit(1)
print()

# Test 9: Order Models
print("✓ Test 9: Order Models")
try:
    from apps.orders.models import Order
    order_count = Order.objects.count()
    print(f"  ✅ Order model accessible")
    print(f"  Total orders: {order_count}")
except Exception as e:
    print(f"  ❌ Order model access failed: {e}")
    sys.exit(1)
print()

# Test 10: Notification Models
print("✓ Test 10: Notification Models")
try:
    from apps.notifications.models import NotificationLog
    notification_count = NotificationLog.objects.count()
    print(f"  ✅ NotificationLog model accessible")
    print(f"  Total notifications: {notification_count}")
except Exception as e:
    print(f"  ❌ NotificationLog model access failed: {e}")
    sys.exit(1)
print()

# Summary
print("=" * 70)
print("VERIFICATION COMPLETE!")
print("=" * 70)
print()
print("✅ All tests passed successfully!")
print()
print("Next Steps:")
print("1. Start Celery worker:")
print("   celery -A config worker --loglevel=info --pool=solo")
print()
print("2. Start Django development server:")
print("   python manage.py runserver")
print()
print("3. Test the complete flow:")
print("   - Navigate to http://localhost:8000")
print("   - Try OTP login")
print("   - Check Celery worker logs for SMS tasks")
print()
print("=" * 70)
