
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.authentication.models import User

print("-" * 80)
print(f"{'MOBILE':<15} | {'ROLE':<10} | {'SUPERUSER':<10} | {'NAME'}")
print("-" * 80)

for user in User.objects.all():
    print(f"{user.mobile_number:<15} | {user.role:<10} | {str(user.is_superuser):<10} | {user.name}")
    
print("-" * 80)
