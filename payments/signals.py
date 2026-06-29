from django.dispatch import receiver

from orders.signals import order_status_changed


@receiver(order_status_changed)
def on_order_completed_disburse(sender, order, new_status, **kwargs):
    """Enqueue agent and vendor disbursements when an order reaches completed."""
    if new_status != "completed":
        return
    from .tasks import disburse_agent_delivery_fee, disburse_vendor_seller_amount
    if order.agent_id:
        disburse_agent_delivery_fee.delay(order.pk)
    disburse_vendor_seller_amount.delay(order.pk)
