from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import Payment
from .services import FapshiCollectionService, FapshiError, settle_payment_from_status


@shared_task
def auto_release_escrow():
    """
    Auto-release escrow for orders stuck at delivered_confirm for > 72 hours.
    Runs hourly. Idempotent: select_for_update + status guard prevent double-release.
    """
    from orders.models import EscrowEvent, Order
    from orders.signals import order_status_changed

    cutoff = timezone.now() - timedelta(hours=72)
    candidates = list(
        Order.objects
        .filter(status="delivered_confirm", updated_at__lt=cutoff, escrow_released=False)
        .select_related("shop__owner", "buyer")
        .values_list("pk", flat=True)
    )

    for pk in candidates:
        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().select_related(
                    "shop__owner", "buyer"
                ).get(pk=pk)
            except Order.DoesNotExist:
                continue
            if order.status != "delivered_confirm" or order.escrow_released:
                continue
            order.status = "completed"
            order.escrow_released = True
            order.save()
            EscrowEvent.objects.create(
                order=order,
                event="released",
                amount=order.total,
                note="Escrow auto-released after 72-hour buyer confirmation window.",
            )
        order_status_changed.send(
            sender=Order,
            order=order,
            old_status="delivered_confirm",
            new_status="completed",
            actor=None,
        )


@shared_task
def reconcile_pending_payments():
    """
    Fapshi fires each webhook once with no retry. If the server was briefly
    unavailable or the verification call failed, orders can get stuck in
    `processing`. This task polls Fapshi for any stuck payments and routes them
    through the same idempotent settle helper used by the webhook.
    """
    cutoff = timezone.now() - timedelta(minutes=10)
    stuck = (
        Payment.objects
        .filter(status="processing", updated_at__lt=cutoff)
        .exclude(external_ref="")
    )
    service = FapshiCollectionService()
    for payment in stuck:
        try:
            txn = service.get_status(payment.external_ref)
        except FapshiError:
            continue
        settle_payment_from_status(payment.external_ref, txn)
