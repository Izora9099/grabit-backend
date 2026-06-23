from django.dispatch import receiver

from orders.signals import order_status_changed


@receiver(order_status_changed)
def on_order_completed_disburse_agent(sender, order, new_status, **kwargs):
    """Enqueue agent delivery-fee disbursement when an order reaches completed."""
    if new_status != "completed" or not order.agent_id:
        return
    from .tasks import disburse_agent_delivery_fee
    disburse_agent_delivery_fee.delay(order.pk)
