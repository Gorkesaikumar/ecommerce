from django.core.management.base import BaseCommand
from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from django.utils import timezone
from datetime import timedelta
import random
import uuid

class Command(BaseCommand):
    help = 'Generates dummy orders for reports testing'

    def handle(self, *args, **options):
        self.stdout.write('Generating dummy data...')
        
        products = list(Product.objects.all())
        if not products:
            self.stdout.write(self.style.ERROR('No products found! Please create products first.'))
            return

        statuses = ['PAID', 'SHIPPED', 'DELIVERED'] # Only "valid" orders for reports
        
        # Last 30 days
        for i in range(50):
            days_ago = random.randint(0, 30)
            order_date = timezone.now() - timedelta(days=days_ago)
            
            # Random amount of items
            num_items = random.randint(1, 4)
            selected_products = random.sample(products, num_items)
            
            total_amount = 0
            
            # Create Order
            order = Order.objects.create(
                id=uuid.uuid4(),
                status=random.choice(statuses),
                total_amount=0, # Will update
                shipping_address={"line1": "123 Test St", "city": "Hyderabad", "zip_code": "500001"},
                guest_email=f"test{i}@example.com"
            )
            # Hack to override auto_now_add
            order.created_at = order_date
            order.save()
            
            for prod in selected_products:
                qty = random.randint(1, 3)
                price = prod.base_price
                
                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    product_snapshot={"name": prod.name},
                    length=10, breadth=10, height=10,
                    unit_price=price,
                    quantity=qty
                )
                total_amount += (price * qty)
            
            order.total_amount = total_amount
            order.save()
            
        self.stdout.write(self.style.SUCCESS(f'Successfully created 50 dummy orders.'))
