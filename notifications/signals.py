from django.dispatch import receiver

from orders.signals import (
    dispute_filed,
    dispute_resolved,
    order_status_changed,
    payment_confirmed,
)
from .models import Notification

# Human-readable labels for order statuses used in notification copy
STATUS_LABELS = {
    "paid_escrow":        "Paid — awaiting preparation",
    "preparing":          "Being prepared",
    "agent_assigned":     "Delivery agent assigned",
    "picked_up":          "Picked up by agent",
    "in_transit":         "Out for delivery",
    "delivered_confirm":  "Delivered — awaiting your confirmation",
    "completed":          "Completed",
    "cancelled":          "Cancelled",
    "refunded":           "Refunded",
    "partially_resolved": "Partially resolved",
    "disputed":           "Under dispute",
}


@receiver(payment_confirmed)
def on_payment_confirmed(sender, payment, order, **kwargs):
    # Notify buyer
    Notification.objects.create(
        user=order.buyer,
        type="order",
        title="Payment confirmed",
        body=f"Your payment of {order.total:,} XAF for order {order.order_id} was received. "
             "The vendor is now preparing your order.",
        href=f"/orders/{order.order_id}",
    )
    # Notify vendor
    Notification.objects.create(
        user=order.shop.owner,
        type="order",
        title=f"New paid order: {order.order_id}",
        body=f"Order {order.order_id} ({order.total:,} XAF) has been paid. Please start preparing it.",
        href=f"/orders/{order.order_id}",
    )


@receiver(order_status_changed)
def on_order_status_changed(sender, order, old_status, new_status, actor, **kwargs):
    label = STATUS_LABELS.get(new_status, new_status)

    if new_status == "agent_assigned" and order.agent:
        # Notify the newly assigned agent
        Notification.objects.create(
            user=order.agent,
            type="delivery",
            title=f"New delivery assignment: {order.order_id}",
            body=f"You have been assigned to deliver order {order.order_id} in {order.city}.",
            href=f"/orders/{order.order_id}",
        )

    if new_status in ("picked_up", "in_transit", "delivered_confirm"):
        # Notify the buyer of delivery progress
        Notification.objects.create(
            user=order.buyer,
            type="delivery",
            title=f"Order {order.order_id}: {label}",
            body=f"Your order {order.order_id} status has been updated to: {label}.",
            href=f"/orders/{order.order_id}",
        )

    if new_status == "completed":
        Notification.objects.create(
            user=order.buyer,
            type="order",
            title=f"Order {order.order_id} complete",
            body="Your order has been marked as completed. Thank you for using GrabIT!",
            href=f"/orders/{order.order_id}",
        )
        Notification.objects.create(
            user=order.shop.owner,
            type="order",
            title=f"Order {order.order_id} completed — payment incoming",
            body=f"Order {order.order_id} is complete. Your payout will be processed shortly.",
            href=f"/orders/{order.order_id}",
        )

    if new_status == "cancelled":
        Notification.objects.create(
            user=order.buyer,
            type="order",
            title=f"Order {order.order_id} cancelled",
            body="Your order has been cancelled. If you were charged, a refund will be processed.",
            href=f"/orders/{order.order_id}",
        )


@receiver(dispute_filed)
def on_dispute_filed(sender, dispute, **kwargs):
    order = dispute.order

    # Notify the vendor
    Notification.objects.create(
        user=order.shop.owner,
        type="dispute",
        title=f"Dispute filed on order {order.order_id}",
        body=f"A dispute has been filed for order {order.order_id}: {dispute.get_reason_display()}. "
             "Our team will review it shortly.",
        href=f"/disputes/{dispute.dispute_id}",
    )


@receiver(dispute_resolved)
def on_dispute_resolved(sender, dispute, **kwargs):
    order = dispute.order
    resolution_label = dispute.get_resolution_display()

    for user in [order.buyer, order.shop.owner]:
        Notification.objects.create(
            user=user,
            type="dispute",
            title=f"Dispute {dispute.dispute_id} resolved",
            body=f"The dispute for order {order.order_id} has been resolved: {resolution_label}.",
            href=f"/disputes/{dispute.dispute_id}",
        )
