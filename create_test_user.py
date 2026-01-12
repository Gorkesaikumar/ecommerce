import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.authentication.models import User

def create_test_user():
    mobile = "+919999999999"
    if not User.objects.filter(mobile_number=mobile).exists():
        User.objects.create_user(mobile_number=mobile, email="test@example.com", name="Test User")
        print(f"Created user {mobile}")
    else:
        print(f"User {mobile} already exists")

if __name__ == "__main__":
    create_test_user()
