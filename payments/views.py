from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Payment, Payout
from .serializers import InitiatePaymentSerializer, PaymentSerializer, PayoutSerializer
from orders.models import Order


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
