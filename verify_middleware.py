
# Simplified Middleware Verification

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from apps.authentication.middleware import JWTCookieMiddleware
from django.contrib.auth.models import AnonymousUser

User = get_user_model()
customer = User(id=999, mobile_number='9999999999', role='CUSTOMER')
customer.save()

# Generate Token
refresh = RefreshToken.for_user(customer)
token = str(refresh.access_token)

# Test 1: Customer Path + Cookie
request = RequestFactory().get('/account/dashboard')
request.COOKIES['access_token'] = token
request.user = AnonymousUser() # Simulate no session

mw = JWTCookieMiddleware(lambda r: None)
mw(request)

print(f"Test 1 (Customer Path): User ID {request.user.id}")
if request.user.id == customer.id:
    print("SUCCESS")
else:
    print("FAILURE")

# Test 2: Admin Path + Cookie (Isolation)
request_admin = RequestFactory().get('/admin/dashboard')
request_admin.COOKIES['access_token'] = token
request_admin.user = AnonymousUser() # Simulate session didn't find admin yet (or did)

mw(request_admin)

print(f"Test 2 (Admin Path): User ID {getattr(request_admin.user, 'id', 'None')}")
if request_admin.user.id is None:
    print("SUCCESS: Middleware ignored JWT on admin path")
else:
    print("FAILURE: Middleware applied JWT on admin path")

customer.delete()
