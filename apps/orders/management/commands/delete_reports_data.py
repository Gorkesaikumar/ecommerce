from django.core.management.base import BaseCommand
from apps.orders.models import Order

class Command(BaseCommand):
    help = 'Deletes dummy orders'

    def handle(self, *args, **options):
        count, _ = Order.objects.filter(guest_email__startswith='test').delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} dummy orders.'))
