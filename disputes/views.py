from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Dispute
from .serializers import DisputeSerializer, DisputeCreateSerializer


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
        dispute.resolution = request.data.get("resolution")
        dispute.admin_note = request.data.get("admin_note", "")
        dispute.status = "resolved"
        dispute.resolved_by = request.user
        from django.utils import timezone
        dispute.resolved_at = timezone.now()
        if dispute.resolution == "release_vendor":
            dispute.order.escrow_released = True
            dispute.order.status = "completed"
            dispute.order.save()
        dispute.save()
        return Response(DisputeSerializer(dispute).data)
