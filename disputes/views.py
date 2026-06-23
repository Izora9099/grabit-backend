import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.images import process_image_upload
from .models import Dispute
from .serializers import DisputeSerializer, DisputeCreateSerializer
from orders.models import EscrowEvent, Order, OrderFinancials
from orders.signals import dispute_filed, dispute_resolved
from payments.models import Payout
from payments.services import FapshiError, FapshiPayoutService

logger = logging.getLogger(__name__)


class DisputeListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        return DisputeCreateSerializer if self.request.method == "POST" else DisputeSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Dispute.objects.all()
        if user.role == "vendor":
            try:
                return Dispute.objects.filter(order__shop=user.shop)
            except AttributeError:
                return Dispute.objects.none()
        return Dispute.objects.filter(opened_by=user)

    def perform_create(self, serializer):
        dispute = serializer.save()
        dispute_filed.send(sender=dispute.__class__, dispute=dispute)


class DisputeDetailView(generics.RetrieveAPIView):
    serializer_class = DisputeSerializer
    lookup_field = "dispute_id"

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Dispute.objects.all()
        if user.role == "vendor":
            try:
                return Dispute.objects.filter(order__shop=user.shop)
            except AttributeError:
                return Dispute.objects.none()
        return Dispute.objects.filter(opened_by=user)


class ResolveDisputeView(APIView):
    """Admin-only: resolve a dispute with a row-level lock to prevent concurrent resolution."""

    def patch(self, request, dispute_id):
        if request.user.role != "admin":
            return Response({"detail": "Admin only."}, status=403)

        resolution = request.data.get("resolution")
        if resolution not in ("release_vendor", "refund_buyer", "partial_refund"):
            return Response({"detail": "Invalid resolution value."}, status=400)

        with transaction.atomic():
            try:
                dispute = Dispute.objects.select_for_update().get(dispute_id=dispute_id)
            except Dispute.DoesNotExist:
                return Response({"detail": "Not found."}, status=404)

            if dispute.status == "resolved":
                return Response({"detail": "Dispute already resolved."}, status=400)

            order = Order.objects.select_for_update().get(pk=dispute.order_id)

            dispute.resolution = resolution
            dispute.admin_note = request.data.get("admin_note", "")
            dispute.status = "resolved"
            dispute.resolved_by = request.user
            dispute.resolved_at = timezone.now()

            if resolution == "release_vendor":
                order.escrow_released = True
                order.status = "completed"
                order.save()
                EscrowEvent.objects.create(
                    order=order,
                    event="released",
                    amount=order.total,
                    note="Released to vendor after dispute resolution.",
                )

            elif resolution == "refund_buyer":
                order.escrow_released = False
                order.status = "refunded"
                order.save()
                EscrowEvent.objects.create(
                    order=order,
                    event="refunded",
                    amount=order.total,
                    note="Full refund issued to buyer after dispute resolution.",
                )

            elif resolution == "partial_refund":
                buyer_amount = request.data.get("buyer_refund_amount")
                vendor_amount = request.data.get("vendor_release_amount")

                if buyer_amount is None or vendor_amount is None:
                    return Response(
                        {"detail": "partial_refund requires buyer_refund_amount and vendor_release_amount."},
                        status=400,
                    )
                try:
                    buyer_amount = int(buyer_amount)
                    vendor_amount = int(vendor_amount)
                except (ValueError, TypeError):
                    return Response({"detail": "Refund amounts must be integers."}, status=400)

                if buyer_amount + vendor_amount != order.total:
                    return Response(
                        {"detail": f"buyer_refund_amount + vendor_release_amount must equal order total ({order.total} XAF)."},
                        status=400,
                    )

                dispute.buyer_refund_amount = buyer_amount
                dispute.vendor_release_amount = vendor_amount

                # Update OrderFinancials with the split for full audit trail
                try:
                    financials = order.financials
                    financials.buyer_refund_amount = buyer_amount
                    financials.vendor_release_amount = vendor_amount
                    financials.save(update_fields=["buyer_refund_amount", "vendor_release_amount"])
                except OrderFinancials.DoesNotExist:
                    pass

                order.escrow_released = True
                order.status = "partially_resolved"
                order.save()
                EscrowEvent.objects.create(
                    order=order,
                    event="partial_refund",
                    amount=buyer_amount,
                    note=f"Partial refund: {buyer_amount} XAF to buyer, {vendor_amount} XAF to vendor. Admin note: {dispute.admin_note}",
                )

            dispute.save()

        # Initiate money movement AFTER commit so a Fapshi error can't roll
        # back the dispute resolution. Failures are logged and surfaced via
        # the Payout row status for manual retry.
        if resolution in ("refund_buyer", "partial_refund"):
            refund_amount = order.total if resolution == "refund_buyer" else buyer_amount
            try:
                phone = order.payment.phone_number
            except Exception:
                phone = None

            if phone:
                payout = Payout.objects.create(
                    recipient=order.buyer,
                    method="mobile money",
                    phone_number=phone,
                    amount=refund_amount,
                    status="processing",
                    payout_date=timezone.now().date(),
                )
                try:
                    FapshiPayoutService().payout(
                        amount=refund_amount,
                        phone=phone,
                        medium="mobile money",
                        user_id=str(order.buyer_id),
                        external_id=f"refund-{order.order_id}",
                        message=f"GrabIT refund — order {order.order_id}",
                    )
                    payout.status = "paid"
                except FapshiError as exc:
                    logger.error("Refund payout failed for order %s: %s", order.order_id, exc)
                    payout.status = "failed"
                payout.save(update_fields=["status"])
            else:
                logger.error(
                    "Cannot initiate refund for order %s: no phone number on payment record.",
                    order.order_id,
                )

        dispute_resolved.send(sender=dispute.__class__, dispute=dispute)
        return Response(DisputeSerializer(dispute).data)


class DisputeEvidenceUploadView(APIView):
    """Upload or replace the evidence file on an existing dispute."""
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, dispute_id):
        try:
            dispute = Dispute.objects.get(dispute_id=dispute_id, opened_by=request.user)
        except Dispute.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        if dispute.status == "resolved":
            return Response({"detail": "Cannot add evidence to a resolved dispute."}, status=400)
        file = request.FILES.get("evidence")
        if not file:
            return Response({"detail": "No file provided."}, status=400)

        # Convert image evidence to WebP; PDFs pass through unchanged
        header = file.read(4)
        file.seek(0)
        if header != b"%PDF":
            try:
                file = process_image_upload(file)
            except DjangoValidationError as exc:
                return Response({"detail": exc.message}, status=400)

        dispute.evidence = file
        dispute.save(update_fields=["evidence"])
        return Response(DisputeSerializer(dispute).data)
