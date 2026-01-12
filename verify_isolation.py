
# Shell Execution Version
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from apps.authentication.middleware import JWTCookieMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware

User = get_user_model()
from rest_framework_simplejwt.tokens import RefreshToken
from apps.authentication.middleware import JWTCookieMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware

User = get_user_model()

# Setup Users
admin_user, _ = User.objects.get_or_create(email='admin@test.com', defaults={'role': 'ADMIN', 'mobile_number': '+918888888888'})
admin_user.set_password('adminpass')
admin_user.save()

customer_user, _ = User.objects.get_or_create(mobile_number='+917777777777', defaults={'role': 'CUSTOMER'})

print("--- 1. Testing Middleware Logic (Mock Request) ---")
# Simulate a request having BOTH Session (Admin) and JWT Cookie (Customer)

factory = RequestFactory()
request = factory.get('/account/dashboard') # Customer Path

# 1. Simulate Session Middleware (Admin Logged In)
middleware = SessionMiddleware(lambda r: None)
middleware.process_request(request)
request.session['_auth_user_id'] = str(admin_user.id)
request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
request.session.save()

# 2. Simulate Auth Middleware (Populates request.user as Admin)
auth_middleware = AuthenticationMiddleware(lambda r: None)
auth_middleware.process_request(request)
print(f"User after AuthMiddleware (Should be Admin): {request.user.role}")

# 3. Request has JWT Cookie (Customer)
refresh = RefreshToken.for_user(customer_user)
token = str(refresh.access_token)
request.COOKIES['access_token'] = token

# 4. Run Our Isolation Middleware
jwt_middleware = JWTCookieMiddleware(lambda r: None)
jwt_middleware(request)

print(f"User after JWTCookieMiddleware (Should be Customer): {request.user.role}")

if request.user.id == customer_user.id:
    print("SUCCESS: Middleware correctly prioritized JWT Cookie for Customer path.")
else:
    print("FAILURE: Middleware did not switch user.")

print("\n--- 2. Testing Admin Path Isolation ---")
admin_request = factory.get('/admin/dashboard')
# Setup Session (Admin)
middleware.process_request(admin_request)
admin_request.session['_auth_user_id'] = str(admin_user.id)
admin_request.session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
auth_middleware.process_request(admin_request)

# Setup JWT (Customer) - Contamination attempt
admin_request.COOKIES['access_token'] = token

# Run Middleware
jwt_middleware(admin_request)
print(f"User on /admin path (Should be Admin): {admin_request.user.role}")

if admin_request.user.id == admin_user.id:
    print("SUCCESS: Middleware ignored JWT on Admin path.")
else:
    print(f"FAILURE: Middleware improperly switched user on Admin path (User: {admin_request.user.role})")

