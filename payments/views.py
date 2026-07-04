import hmac

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminRole
from orders.models import Order, OrderFinancials
from shops.models import Shop
from .models import Payment, Payout, PlatformConfig, ProcessedWebhook
from .serializers import InitiatePaymentSerializer, PayoutSerializer, PayoutRequestSerializer, PlatformConfigSerializer
from .services import FapshiCollectionService, FapshiPayoutService, FapshiError, settle_payment_from_status

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


class PayoutListView(generics.ListAPIView):
    serializer_class = PayoutSerializer

    def get_queryset(self):
        return Payout.objects.filter(recipient=self.request.user)


PAYOUT_MEDIUM_MAP = {"mtn_momo": "mobile money", "orange_money": "orange money"}


class VendorBalanceView(APIView):
    """Returns the vendor's available payout balance and escrow summary."""

    def get(self, request):
        if request.user.role != "vendor":
            return Response({"detail": "Vendors only."}, status=status.HTTP_403_FORBIDDEN)
        try:
            shop = request.user.shop
        except Exception:
            return Response({"available": 0, "in_escrow": 0, "total_paid_out": 0})

        # Total earned: seller_amount from all escrow-released orders
        earned = (
            OrderFinancials.objects
            .filter(order__shop=shop, order__escrow_released=True)
            .aggregate(total=Sum("seller_amount"))["total"] or 0
        )

        # In escrow: seller_amount from paid-but-not-yet-released orders
        in_escrow = (
            OrderFinancials.objects
            .filter(order__shop=shop, order__escrow_released=False,
                    order__status__in=["paid_escrow", "preparing", "agent_assigned",
                                       "picked_up", "in_transit", "delivered_confirm"])
            .aggregate(total=Sum("seller_amount"))["total"] or 0
        )

        # Already paid out or reserved (processing = reserved, not yet confirmed by Fapshi)
        paid_out = (
            Payout.objects
            .filter(recipient=request.user, status__in=["paid", "processing"])
            .aggregate(total=Sum("amount"))["total"] or 0
        )

        return Response({
            "available": max(0, earned - paid_out),
            "in_escrow": in_escrow,
            "total_paid_out": paid_out,
        })


class PayoutRequestView(APIView):
    """Vendor requests a payout — validates balance, calls Fapshi /payout."""

    def post(self, request):
        if request.user.role != "vendor":
            return Response({"detail": "Vendors only."}, status=status.HTTP_403_FORBIDDEN)
        try:
            shop = request.user.shop
        except Exception:
            return Response({"detail": "No shop found."}, status=status.HTTP_404_NOT_FOUND)

        if not getattr(settings, "FAPSHI_PAYOUT_API_USER", ""):
            return Response(
                {"detail": "Payout service not yet activated. Contact support."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = PayoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        method = serializer.validated_data["method"]
        phone  = serializer.validated_data["phone"]

        # Recompute available balance under a lock to prevent race conditions.
        # Lock the shop row itself (not just existing Payout rows) so two
        # concurrent *first* payout requests — where there's nothing yet to
        # lock via select_for_update() on Payout — still serialize.
        with transaction.atomic():
            Shop.objects.select_for_update().get(pk=shop.pk)
            earned = (
                OrderFinancials.objects
                .filter(order__shop=shop, order__escrow_released=True)
                .aggregate(total=Sum("seller_amount"))["total"] or 0
            )
            paid_out = (
                Payout.objects
                .filter(recipient=request.user, status__in=["paid", "processing"])
                .aggregate(total=Sum("amount"))["total"] or 0
            )
            available = max(0, earned - paid_out)

            if amount > available:
                return Response(
                    {"detail": f"Insufficient balance. Available: {available:,} XAF."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payout = Payout.objects.create(
                recipient=request.user,
                method=method,
                phone_number=phone,
                amount=amount,
                status="processing",
                payout_date=timezone.now().date(),
            )

        # Call Fapshi outside the lock
        service = FapshiPayoutService()
        try:
            service.payout(
                amount=amount,
                phone=phone,
                medium=PAYOUT_MEDIUM_MAP[method],
                user_id=str(request.user.id),
                external_id=payout.payout_id,
                message=f"GrabIT vendor payout {payout.payout_id}",
            )
            payout.status = "paid"
            payout.save(update_fields=["status"])
        except FapshiError as e:
            payout.status = "failed"
            payout.save(update_fields=["status"])
            return Response(
                {"detail": f"Payout failed: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(PayoutSerializer(payout).data, status=status.HTTP_201_CREATED)


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


class PlatformConfigView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(PlatformConfigSerializer(PlatformConfig.get()).data)

    def patch(self, request):
        cfg = PlatformConfig.get()
        serializer = PlatformConfigSerializer(cfg, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
