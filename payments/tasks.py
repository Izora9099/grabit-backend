import logging
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import Payment, Payout, PlatformConfig
from .services import FapshiCollectionService, FapshiError, FapshiPayoutService, settle_payment_from_status

logger = logging.getLogger(__name__)


@shared_task
def auto_release_escrow():
    """
    Auto-release escrow for orders stuck at delivered_confirm for > 72 hours.
    Runs hourly. Idempotent: select_for_update + status guard prevent double-release.
    """
    from orders.models import EscrowEvent, Order
    from orders.signals import order_status_changed

    hours = PlatformConfig.get().escrow_release_hours
    cutoff = timezone.now() - timedelta(hours=hours)
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
                note=f"Escrow auto-released after {hours}-hour buyer confirmation window.",
            )
        order_status_changed.send(
            sender=Order,
            order=order,
            old_status="delivered_confirm",
            new_status="completed",
            actor=None,
        )


@shared_task
def disburse_agent_delivery_fee(order_pk):
    """
    Pays the delivery fee to the assigned agent after order completion.
    Creates a Payout row before calling Fapshi so a network failure doesn't
    leave the disbursement unrecorded.
    """
    from orders.models import Order

    try:
        order = (
            Order.objects
            .select_related("agent", "financials")
            .get(pk=order_pk)
        )
    except Order.DoesNotExist:
        return

    if not order.agent_id:
        return

    try:
        fee = order.financials.delivery_fee
    except Exception:
        logger.error("disburse_agent_delivery_fee: no OrderFinancials for order pk=%s", order_pk)
        return

    if fee < 100:
        return

    agent = order.agent
    if not agent.phone:
        logger.error(
            "disburse_agent_delivery_fee: agent %s has no phone number, cannot pay order %s",
            agent.id, order.order_id,
        )
        return

    payout = Payout.objects.create(
        recipient=agent,
        method="mobile money",
        phone_number=agent.phone,
        amount=fee,
        status="processing",
        payout_date=timezone.now().date(),
    )
    try:
        FapshiPayoutService().payout(
            amount=fee,
            phone=agent.phone,
            medium="mobile money",
            user_id=str(agent.id),
            external_id=payout.payout_id,
            message=f"GrabIT delivery fee — order {order.order_id}",
        )
        payout.status = "paid"
    except FapshiError as exc:
        logger.error(
            "disburse_agent_delivery_fee: Fapshi payout failed for order %s: %s",
            order.order_id, exc,
        )
        payout.status = "failed"
    payout.save(update_fields=["status"])


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
