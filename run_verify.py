
from apps.products.models import CustomizeRequest, Product
from apps.products.serializers import CustomizeRequestSerializer
from apps.products.admin_views import AdminCustomizeRequestViewSet
from apps.authentication.models import User
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError

# Setup Data
user = User.objects.filter(role='ADMIN').first()
if not user:
    print("No Admin user found. Creating dummy.")
    user = User.objects.create(mobile_number='+919999999999', role='ADMIN')

product = Product.objects.first()

print("--- 1. Testing Creation Security ---")
data = {
    'product': product.id,
    'name': 'Test User',
    'email': 'test@example.com',
    'phone': '1234567890',
    'length': 10, 'breadth': 10, 'height': 10,
    'status': 'ACCEPTED' # Attempt to injection
}
serializer = CustomizeRequestSerializer(data=data)
if serializer.is_valid():
    req = serializer.save(user=user)
    print(f"Created Request Status: {req.status}")
    if req.status == 'PENDING':
        print("SUCCESS: Status injection blocked. Defaulted to PENDING.")
    else:
        print(f"FAILURE: Status injected as {req.status}")
else:
    print(f"Creation Failed: {serializer.errors}")

print("\n--- 2. Testing Valid Transition (PENDING -> ACCEPTED) ---")
view = AdminCustomizeRequestViewSet()
view.request = APIRequestFactory().patch(f'/customize-requests/{req.id}/', {'status': 'ACCEPTED'})
view.request.user = user
view.kwargs = {'pk': req.id}
view.format_kwarg = None

# Mocking the object since perform_update calls self.get_object()
view.get_object = lambda: req

try:
    s = CustomizeRequestSerializer(req, data={'status': 'ACCEPTED'}, partial=True)
    if s.is_valid():
        view.perform_update(s)
        print(f"Updated Status: {req.status}")
        if req.status == 'ACCEPTED':
            print("SUCCESS: Transition to ACCEPTED allowed.")
    else:
        print(f"Validation Failed: {s.errors}")
except Exception as e:
    print(f"FAILURE: Exception {e}")

print("\n--- 3. Testing Invalid Transition (ACCEPTED -> REJECTED) ---")
# req is now ACCEPTED
try:
    s = CustomizeRequestSerializer(req, data={'status': 'REJECTED'}, partial=True)
    if s.is_valid():
        view.perform_update(s)
        print("FAILURE: Allowed transition from ACCEPTED to REJECTED.")
    else:
        print("Validation failed (Expected?)")
except ValidationError as e:
    print(f"SUCCESS: Blocked transition. Error: {e}")
except Exception as e:
    print(f"EXCEPTION: {e}")

# Cleanup
req.delete()
