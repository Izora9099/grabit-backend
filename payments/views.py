import hmac

from django.conf import settings
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from .models import Payment, Payout, ProcessedWebhook
from .serializers import InitiatePaymentSerializer, PayoutSerializer
from .services import FapshiCollectionService, FapshiError, settle_payment_from_status

MEDIUM_MAP = {"mtn_momo": "mobile money", "orange_money": "orange money"}


@method_decorator(ratelimit(key="user", rate="5/m", method="POST", block=True), name="post")
class InitiatePaymentView(APIView):
    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = serializer.validated_data["method"]
        phone = serializer.validated_data["phone_number"]

        # --- Phase 1: claim the slot under a short lock, then release ---
        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().get(
                    order_id=serializer.validated_data["order_id"],
                    buyer=request.user,
                )
            except Order.DoesNotExist:
                return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

            if order.status != "awaiting_payment":
                return Response(
                    {"detail": "Order is not awaiting payment."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payment, _ = Payment.objects.get_or_create(
                order=order,
                defaults={"method": method, "amount": order.total, "phone_number": phone},
            )
            if payment.status == "paid":
                return Response(
                    {"detail": "Payment already completed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if payment.status == "processing":
                return Response(
                    {"detail": "A payment is already in progress."},
                    status=status.HTTP_409_CONFLICT,
                )

            payment.status = "processing"
            payment.method = method
            payment.phone_number = phone
            payment.save(update_fields=["status", "method", "phone_number"])

        # --- Phase 2: call Fapshi OUTSIDE the lock ---
        service = FapshiCollectionService()
        try:
            trans_id = service.direct_pay(
                amount=order.total,
                phone=phone,
                external_id=str(order.order_id),
                medium=MEDIUM_MAP[method],
                user_id=str(request.user.id),
                message=f"GrabIT order {order.order_id}",
            )
        except FapshiError as e:
            payment.status = "failed"
            payment.save(update_fields=["status"])
            print(f"FAPSHI ERROR [{order.order_id}] status={e.status_code} payload={e.payload} msg={e}", flush=True)
            return Response(
                {"detail": f"Could not initiate payment: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payment.external_ref = trans_id
        payment.save(update_fields=["external_ref"])

        return Response(
            {
                "detail": "Payment request sent. Confirm the prompt on your phone.",
                "transId": trans_id,
                "status": "processing",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class FapshiPingView(APIView):
    """Temp diagnostic: tests Fapshi connectivity from Railway's network. Remove after diagnosis."""
    def get(self, request):
        import requests as req_lib
        from django.conf import settings
        import traceback as tb
        base = settings.FAPSHI_BASE_URL.rstrip("/")
        headers = {
            "apiuser": settings.FAPSHI_API_USER,
            "apikey": settings.FAPSHI_API_KEY,
            "Content-Type": "application/json",
        }
        try:
            r = req_lib.post(
                base + "/direct-pay",
                json={"amount": 100, "phone": "670000000", "externalId": "PING-TEST-1", "medium": "mobile money"},
                headers=headers,
                timeout=30,
            )
            return Response({"status": r.status_code, "body": r.json() if r.content else {}})
        except req_lib.exceptions.SSLError as e:
            return Response({"error": "SSLError", "detail": str(e)}, status=502)
        except req_lib.exceptions.Timeout:
            return Response({"error": "Timeout", "detail": "30s timeout reached"}, status=504)
        except req_lib.exceptions.ConnectionError as e:
            return Response({"error": "ConnectionError", "detail": str(e)}, status=502)
        except Exception as e:
            return Response({"error": type(e).__name__, "detail": str(e), "trace": tb.format_exc()}, status=500)


class PayoutListView(generics.ListAPIView):
    serializer_class = PayoutSerializer

    def get_queryset(self):
        return Payout.objects.filter(recipient=self.request.user)


@method_decorator(csrf_exempt, name="dispatch")
class FapshiWebhookView(APIView):
    """
    Receives Fapshi payment notifications.

    Security model:
    - Shared secret in x-wh-secret header (not HMAC — Fapshi does not sign bodies).
    - Every webhook is re-verified via GET /payment-status before any state change.
    - Idempotency key is "<transId>:<verified_status>" so a status change is only
      applied once even if Fapshi fires the webhook multiple times.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        # 1. Verify shared secret
        secret = getattr(settings, "FAPSHI_WEBHOOK_SECRET", "")
        received = request.headers.get("x-wh-secret", "")
        if not secret or not hmac.compare_digest(secret, received):
            return Response({"detail": "Invalid webhook secret."}, status=status.HTTP_401_UNAUTHORIZED)

        trans_id = request.data.get("transId")
        if not trans_id:
            return Response({"detail": "Missing transId."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Re-verify with Fapshi — never trust the webhook body.
        service = FapshiCollectionService()
        try:
            txn = service.get_status(trans_id)
        except FapshiError:
            # Can't verify right now; the reconciliation task will catch it.
            return Response({"detail": "Could not verify; will reconcile later."}, status=status.HTTP_200_OK)

        # 3. Idempotency — keyed on verified (not claimed) status.
        dedupe_key = f"{trans_id}:{txn.get('status')}"
        _, created = ProcessedWebhook.objects.get_or_create(trans_id=dedupe_key)
        if not created:
            return Response({"detail": "Already processed."}, status=status.HTTP_200_OK)

        settle_payment_from_status(trans_id, txn)
        return Response({"detail": "OK."}, status=status.HTTP_200_OK)
