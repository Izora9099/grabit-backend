from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import Dispute
from .serializers import DisputeSerializer, DisputeCreateSerializer
from orders.models import EscrowEvent


class DisputeListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        return DisputeCreateSerializer if self.request.method == "POST" else DisputeSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Dispute.objects.all()
        return Dispute.objects.filter(opened_by=user)


class DisputeDetailView(generics.RetrieveAPIView):
    serializer_class = DisputeSerializer
    lookup_field = "dispute_id"

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Dispute.objects.all()
        return Dispute.objects.filter(opened_by=user)


class ResolveDisputeView(APIView):
    """Admin-only: resolve a dispute."""
    def patch(self, request, dispute_id):
        if request.user.role != "admin":
            return Response({"detail": "Admin only."}, status=403)
        dispute = Dispute.objects.get(dispute_id=dispute_id)
        resolution = request.data.get("resolution")
        if resolution not in ("release_vendor", "refund_buyer", "partial_refund"):
            return Response({"detail": "Invalid resolution value."}, status=400)

        dispute.resolution = resolution
        dispute.admin_note = request.data.get("admin_note", "")
        dispute.status = "resolved"
        dispute.resolved_by = request.user
        dispute.resolved_at = timezone.now()

        order = dispute.order
        if resolution == "release_vendor":
            order.escrow_released = True
            order.status = "completed"
            order.save()
            EscrowEvent.objects.create(
                order=order, event="released", amount=order.total,
                note="Released to vendor after dispute resolution.",
            )
        elif resolution == "refund_buyer":
            order.escrow_released = False
            order.status = "refunded"
            order.save()
            EscrowEvent.objects.create(
                order=order, event="refunded", amount=order.total,
                note="Full refund issued to buyer after dispute resolution.",
            )
        elif resolution == "partial_refund":
            order.escrow_released = True
            order.status = "partially_resolved"
            order.save()
            EscrowEvent.objects.create(
                order=order, event="partial_refund", amount=order.total,
                note=f"Partial refund. Admin note: {dispute.admin_note}",
            )

        dispute.save()
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
        dispute.evidence = file
        dispute.save(update_fields=["evidence"])
        return Response(DisputeSerializer(dispute).data)
