import hashlib
import hmac

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from .models import Payment, Payout, ProcessedWebhook
from .serializers import InitiatePaymentSerializer, PaymentSerializer, PayoutSerializer


@method_decorator(ratelimit(key="user", rate="5/m", method="POST", block=True), name="post")
class InitiatePaymentView(APIView):
    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = Order.objects.get(order_id=serializer.validated_data["order_id"], buyer=request.user)
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                "method": serializer.validated_data["method"],
                "amount": order.total,
                "phone_number": serializer.validated_data.get("phone_number", ""),
            }
        )
        # TODO: integrate real MTN MoMo / Orange Money SDK here
        # For now, simulate success
        payment.status = "paid"
        payment.external_ref = f"MOCK-{order.order_id}"
        payment.save()
        order.status = "paid_escrow"
        order.save()
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PayoutListView(generics.ListAPIView):
    serializer_class = PayoutSerializer

    def get_queryset(self):
        return Payout.objects.filter(recipient=self.request.user)


@method_decorator(csrf_exempt, name="dispatch")
class FapshiWebhookView(APIView):
    """
    Receives Fapshi payment notifications.

    Security:
    - Authenticates via HMAC-SHA256 signature (X-Fapshi-Signature header)
    - Idempotent: duplicate transIds return 200 immediately without reprocessing
    - No JWT auth — authenticates via signature alone
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        # 1. Verify HMAC signature
        secret = getattr(settings, "FAPSHI_WEBHOOK_SECRET", "")
        if not secret:
            return Response({"detail": "Webhook not configured."}, status=500)

        raw_body = request.body
        received_sig = request.headers.get("X-Fapshi-Signature", "")
        expected_sig = hmac.new(
            secret.encode(), raw_body, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, received_sig):
            return Response({"detail": "Invalid signature."}, status=status.HTTP_401_UNAUTHORIZED)

        # 2. Parse payload
        payload = request.data
        trans_id = payload.get("transId") or payload.get("transactionId")
        event_status = payload.get("status", "")

        if not trans_id:
            return Response({"detail": "Missing transId."}, status=400)

        # 3. Idempotency — insert before processing; reject duplicates
        try:
            ProcessedWebhook.objects.create(trans_id=trans_id)
        except IntegrityError:
            # Already processed — acknowledge without reprocessing
            return Response({"detail": "Already processed."}, status=200)

        # 4. Process the event inside a transaction with a row-level lock
        if event_status == "SUCCESSFUL":
            with transaction.atomic():
                try:
                    payment = Payment.objects.select_for_update().get(external_ref=trans_id)
                except Payment.DoesNotExist:
                    return Response({"detail": "Payment not found."}, status=404)

                if payment.status != "paid":
                    payment.status = "paid"
                    payment.save(update_fields=["status"])
                    order = Order.objects.select_for_update().get(pk=payment.order_id)
                    if order.status == "awaiting_payment":
                        order.status = "paid_escrow"
                        order.save(update_fields=["status"])

        return Response({"detail": "OK."}, status=200)
