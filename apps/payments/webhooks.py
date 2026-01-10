from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Payment
from apps.orders.models import Order
from .services import RazorpayService
from apps.core.services.redis_service import RedisService
import logging
import json

logger = logging.getLogger('audit')

class RobustRazorpayWebhookView(APIView):
    """
    Secure, Idempotent, and Concurrency-Safe Webhook Handler.
    """
    permission_classes = [AllowAny]
    authentication_classes = [] # Explicitly disable auth

    def post(self, request):
        # 1. VERIFY SIGNATURE
        # We must read body as bytes for signature verification
        payload_body = request.body.decode('utf-8')
        signature = request.headers.get('X-Razorpay-Signature')

        if not signature:
             logger.warning("Webhook: Missing Signature")
             return Response({"error": "Missing Signature"}, status=status.HTTP_400_BAD_REQUEST)

        # Verify logic inside service (wraps razorpay client verify)
        try:
             # Ideally pass raw body and signature
             client = RazorpayService.get_client()
             client.utility.verify_webhook_signature(payload_body, signature, client.auth[1]) # Auth[1] is secret
        except Exception as e:
             logger.warning(f"Webhook: Invalid Signature from IP {self._get_client_ip(request)}")
             return Response({"error": "Invalid Signature"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. PARSE PAYLOAD
        try:
            payload = json.loads(payload_body)
            event_type = payload.get('event')
            event_id = payload.get('payload').get('payment').get('entity').get('id') # Using payment_id or event_id? 
            # Razorpay sends a distinct 'x-razorpay-event-id' header or we can construct one from payload
            # Better to use the unique event ID from the payload wrapper if available, else construct unique key
            # payload['contains'] usually has array of entities.
            # Let's use payload['payload']['payment']['entity']['id'] + event_type as key for simplicity 
            # Or better, Razorpay sends 'x-razorpay-event-id' header usually. Let's check payload structure.
            # Payload has { "event": "...", "payload": { ... } }
            # We will use payment_id:event as idempotency key
            
            payment_entity = payload['payload']['payment']['entity']
            rz_order_id = payment_entity['order_id']
            rz_payment_id = payment_entity['id']
            
            idempotency_key = f"{rz_payment_id}:{event_type}"

        except (KeyError, json.JSONDecodeError):
            return Response({"status": "ignored_malformed"}, status=status.HTTP_200_OK)

        # 3. IDEMPOTENCY CHECK
        # TTL 24 hours. Returns True if NEW, False if ALREADY PROCESSED.
        if not RedisService.check_and_set_idempotency_key("webhook", idempotency_key, ttl=86400):
            logger.info(f"Webhook: Duplicate Event Ignored {idempotency_key}")
            return Response({"status": "ignored_duplicate"}, status=status.HTTP_200_OK)

        # 4. DISTRIBUTED LOCKING & PROCESSING
        # Lock on the ORDER ID to prevent race condition with Frontend Success Page
        # We need to find the internal Order ID via Payment table or Notes
        
        try:
            # Finding internal order might require DB lookup if not in notes
            # We stored razopray_order_id in Payment table.
            payment_record = Payment.objects.get(razorpay_order_id=rz_order_id)
            order_id = str(payment_record.order.id)
            
            with RedisService.acquire_lock("order", order_id, timeout=30):
                self._process_event(event_type, payment_record, payment_entity)

        except Payment.DoesNotExist:
            logger.error(f"Webhook: Unknown Order {rz_order_id}")
            # Return 200 to satisfy Razorpay retry policy (otherwise it keeps retrying)
            return Response({"status": "unknown_order"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Webhook: Processing Error {e}")
            # If lock failed or DB error, we might want to return 500 to trigger retry (if not lock timeout)
            # But for lock timeout (race condition), ideally we check DB status.
            return Response({"status": "error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"status": "processed"}, status=status.HTTP_200_OK)

    def _process_event(self, event_type, payment_record, payment_entity):
        # RELOAD DB record to get latest state inside lock
        payment_record.refresh_from_db()
        order = payment_record.order

        if event_type == 'payment.captured':
            if payment_record.status == Payment.Status.CAPTURED:
                logger.info(f"Webhook: Already Captured {payment_record.id}")
                return

            with transaction.atomic():
                payment_record.razorpay_payment_id = payment_entity['id']
                payment_record.status = Payment.Status.CAPTURED
                payment_record.save()
                
                if order.status != Order.Status.PAID:
                    order.status = Order.Status.PAID
                    order.save()
                    logger.info(f"Webhook: Order {order.id} marked PAID")

        elif event_type == 'payment.failed':
            if payment_record.status == Payment.Status.FAILED:
                return

            with transaction.atomic():
                payment_record.status = Payment.Status.FAILED
                payment_record.save()
                
                # CRITICAL: Rollback stock on payment failure
                from apps.products.models import Product
                for item in order.items.all():
                    product = Product.objects.select_for_update().get(id=item.product.id)
                    product.stock_quantity += item.quantity
                    product.save()
                    logger.info(f"Webhook: Restored {item.quantity} units of {product.name}")
                
                logger.info(f"Webhook: Payment Failed {payment_record.id}, Stock Restored")
        
        elif event_type == 'refund.processed' or event_type == 'payment.refunded':
            # Handle refund webhook
            if payment_record.status == Payment.Status.REFUNDED:
                return
            
            with transaction.atomic():
                payment_record.status = Payment.Status.REFUNDED
                payment_record.save()
                
                # Restore stock on refund
                from apps.products.models import Product
                for item in order.items.all():
                    product = Product.objects.select_for_update().get(id=item.product.id)
                    product.stock_quantity += item.quantity
                    product.save()
                
                logger.info(f"Webhook: Refund processed {payment_record.id}, Stock Restored")

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
