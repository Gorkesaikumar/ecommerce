"""
Create admin user with email and password for testing
"""

from django.core.management.base import BaseCommand
from apps.authentication.models import User


class Command(BaseCommand):
    help = 'Create or update admin user with email and password'

    def handle(self, *args, **options):
        email = 'admin@woodcraft.com'
        mobile =  '9876543210'
        password = 'Admin@123'
        
        try:
            # Try to get existing user
            try:
                user = User.objects.get(mobile_number=mobile)
                self.stdout.write(f'Found existing user: {mobile}')
            except User.DoesNotExist:
                # Create new user
                user = User.objects.create_user(
                    mobile_number=mobile,
                    password=password
                )
                self.stdout.write(f'Created new user: {mobile}')
            
            # Update user fields
            user.email = email
            user.role = User.Roles.ADMIN
            user.name = 'Admin User'
            user.is_staff = True
            user.is_active = True
            user.set_password(password)  # Ensure password is hashed
            user.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ Admin user ready!\n'
                f'Email: {email}\n'
                f'Password: {password}\n'
                f'Mobile: {mobile}\n'
                f'Role: {user.role}\n'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
