
from apps.products.models import CustomizeRequest
from apps.products.serializers import CustomizeRequestSerializer
from apps.products.admin_views import AdminCustomizeRequestViewSet
from rest_framework.exceptions import ValidationError

# Mock View
view = AdminCustomizeRequestViewSet()

# Manual Test Object
class MockReq:
    def __init__(self, status):
        self.status = status
        self.id = 1
    def save(self): pass

req = MockReq('ACCEPTED')
view.get_object = lambda: req
view.request = type('obj', (object,), {'user': None})
view._get_client_ip = lambda r: '127.0.0.1'

# Mock Serializer to avoid DB
class MockSerializer:
    def __init__(self, validated_data):
        self.validated_data = validated_data
    def save(self):
        req.status = self.validated_data.get('status')
        return req

print(f"Initial Status: {req.status}")

try:
    # Mimic perform_update logic directly to test logic, bypassing framework overhead
    instance = view.get_object()
    old_status = instance.status
    new_status = 'REJECTED'
    
    print(f"Old: {old_status}, New: {new_status}")
    
    if new_status and new_status != old_status:
        valid_start_states = ['PENDING', 'SUBMITTED']
        if old_status not in valid_start_states:
            if old_status in ['ACCEPTED', 'REJECTED', 'COMPLETED']:
                print("Logic Check: SHOULD RAISE ERROR")
                raise ValidationError("Detected Finalized State")
            else:
                print(f"Logic Warning: old_status {old_status} not in finalized list?")
        else:
            print("Logic Check: Valid start state")
            
    # Now run the actual method if above matches expectation
    # But wait, we need to pass a serializer to perform_update.
    # The actual perform_update calls serializer.save() at the end.
    
except ValidationError as e:
    print(f"Caught Expected Error: {e}")
except Exception as e:
    print(f"Caught Unexpected Error: {e}")
