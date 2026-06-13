from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import Payment
from .services import FapshiCollectionService, FapshiError, settle_payment_from_status


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
