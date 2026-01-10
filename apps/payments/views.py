from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Payment
from .services import RazorpayService
from .serializers import CreatePaymentSerializer, VerifyPaymentSerializer
from apps.orders.models import Order
import logging

logger = logging.getLogger(__name__)

class CreateRazorpayOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        internal_order_id = serializer.validated_data['order_id']
        order = get_object_or_404(Order, id=internal_order_id, user=request.user)

        if order.status != Order.Status.PENDING:
            return Response({"error": "Order is not in pending state"}, status=status.HTTP_400_BAD_REQUEST)

        # Idempotency Check
        if hasattr(order, 'payment'):
             return Response({
                 "razorpay_order_id": order.payment.razorpay_order_id,
                 "amount": order.payment.amount,
                 "currency": order.payment.currency
             })

        try:
            rz_order = RazorpayService.create_order(float(order.total_amount), str(order.id))
            
            Payment.objects.create(
                order=order,
                razorpay_order_id=rz_order['id'],
                amount=order.total_amount,
                currency=rz_order['currency'],
                status=Payment.Status.CREATED
            )
            
            order.status = Order.Status.AWAITING_PAYMENT
            order.save()

            return Response({
                "razorpay_order_id": rz_order['id'],
                "amount": rz_order['amount'], # in paise
                "currency": rz_order['currency'],
                "key_id": settings.RAZORPAY_KEY_ID
            })
        except Exception as e:
            logger.error(f"Payment Init Error: {e}")
            return Response({"error": "Failed to initiate payment"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Verify Signature
        if not RazorpayService.verify_signature(data):
            return Response({"error": "Invalid Signature"}, status=status.HTTP_400_BAD_REQUEST)

        # Update DB
        with transaction.atomic():
            payment = get_object_or_404(Payment, razorpay_order_id=data['razorpay_order_id'])
            
            # Security: Verify the payment belongs to the requesting user
            if payment.order.user != request.user:
                logger.warning(f"Unauthorized payment verification attempt: {request.user.id} for order {payment.order.id}")
                return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
            
            if payment.status == Payment.Status.CAPTURED:
                return Response({"message": "Already captured"}, status=status.HTTP_200_OK)

            payment.razorpay_payment_id = data['razorpay_payment_id']
            payment.razorpay_signature = data['razorpay_signature']
            payment.status = Payment.Status.CAPTURED
            payment.save()
            
            payment.order.status = Order.Status.PAID
            payment.order.save()

        return Response({"status": "Payment Verified"}, status=status.HTTP_200_OK)

class RazorpayWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # In a real impl, retrieve signature from header 'X-Razorpay-Signature'
        # and verify strictly.
        payload = request.data
        
        # Simple extraction for demo. 
        # Real webhook logic requires raw body verif.
        event = payload.get('event')
        
        if event == 'payment.captured':
            payment_entity = payload['payload']['payment']['entity']
            rz_order_id = payment_entity['order_id']
            
            try:
                payment = Payment.objects.get(razorpay_order_id=rz_order_id)
                if payment.status != Payment.Status.CAPTURED:
                    payment.status = Payment.Status.CAPTURED
                    payment.save()
                    payment.order.status = Order.Status.PAID
                    payment.order.save()
                    logger.info(f"Webhook: Captured Order {payment.order.id}")
            except Payment.DoesNotExist:
                logger.error(f"Webhook: Payment not found for {rz_order_id}")

        return Response({"status": "ok"})
