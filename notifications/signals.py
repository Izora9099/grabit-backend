import logging

from django.conf import settings
from django.core.mail import send_mail
from django.dispatch import receiver

logger = logging.getLogger(__name__)

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
    buyer_body = (
        f"Your payment of {order.total:,} XAF for order {order.order_id} was received. "
        "The vendor is now preparing your order."
    )
    vendor_body = (
        f"Order {order.order_id} ({order.total:,} XAF) has been paid. Please start preparing it."
    )

    Notification.objects.create(
        user=order.buyer,
        type="order",
        title="Payment confirmed",
        body=buyer_body,
        href=f"/orders/{order.order_id}",
    )
    try:
        send_mail(
            subject=f"[GrabIT] Payment confirmed — {order.order_id}",
            message=buyer_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.buyer.email],
        )
    except Exception as e:
        logger.error("Failed to send payment_confirmed email to %s: %s", order.buyer.email, e)

    Notification.objects.create(
        user=order.shop.owner,
        type="order",
        title=f"New paid order: {order.order_id}",
        body=vendor_body,
        href=f"/orders/{order.order_id}",
    )
    try:
        send_mail(
            subject=f"[GrabIT] New paid order: {order.order_id}",
            message=vendor_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.shop.owner.email],
        )
    except Exception as e:
        logger.error("Failed to send payment_confirmed email to %s: %s", order.shop.owner.email, e)


@receiver(order_status_changed)
def on_order_status_changed(sender, order, old_status, new_status, actor, **kwargs):
    label = STATUS_LABELS.get(new_status, new_status)

    # In the first-claim model order.agent is None when status becomes agent_assigned
    # (the agent self-assigns by picking up). Notify the claiming agent at picked_up,
    # when order.agent has already been set and saved.
    if new_status == "picked_up" and order.agent:
        Notification.objects.create(
            user=order.agent,
            type="delivery",
            title=f"Delivery claimed: {order.order_id}",
            body=f"You have claimed order {order.order_id} in {order.city}. Head to the vendor for pickup.",
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
        try:
            from analytics.tasks import record_event
            record_event.delay("order_completed", order.shop_id, None, order.buyer_id)
        except Exception:
            pass

        buyer_body = "Your order has been marked as completed. Thank you for using GrabIT!"
        vendor_body = f"Order {order.order_id} is complete. Your payout will be processed shortly."

        Notification.objects.create(
            user=order.buyer,
            type="order",
            title=f"Order {order.order_id} complete",
            body=buyer_body,
            href=f"/orders/{order.order_id}",
        )
        try:
            send_mail(
                subject=f"[GrabIT] Order {order.order_id} completed",
                message=buyer_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.buyer.email],
            )
        except Exception as e:
            logger.error("Failed to send order_completed email to %s: %s", order.buyer.email, e)

        Notification.objects.create(
            user=order.shop.owner,
            type="order",
            title=f"Order {order.order_id} completed — payment incoming",
            body=vendor_body,
            href=f"/orders/{order.order_id}",
        )
        try:
            send_mail(
                subject=f"[GrabIT] Order {order.order_id} completed — payout incoming",
                message=vendor_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.shop.owner.email],
            )
        except Exception as e:
            logger.error("Failed to send order_completed email to %s: %s", order.shop.owner.email, e)

    if new_status == "preparing" and old_status == "agent_assigned":
        # Agent declined — notify vendor so they can reassign
        Notification.objects.create(
            user=order.shop.owner,
            type="delivery",
            title=f"Agent declined order {order.order_id}",
            body=f"The assigned agent declined order {order.order_id}. Please reassign a delivery agent.",
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
        if old_status == "agent_assigned" and order.agent:
            Notification.objects.create(
                user=order.agent,
                type="delivery",
                title=f"Delivery assignment cancelled: {order.order_id}",
                body=f"Order {order.order_id} has been cancelled. Your delivery assignment has been removed.",
                href=f"/orders/{order.order_id}",
            )


@receiver(dispute_filed)
def on_dispute_filed(sender, dispute, **kwargs):
    order = dispute.order
    vendor_body = (
        f"A dispute has been filed for order {order.order_id}: {dispute.get_reason_display()}. "
        "Our team will review it shortly."
    )

    Notification.objects.create(
        user=order.shop.owner,
        type="dispute",
        title=f"Dispute filed on order {order.order_id}",
        body=vendor_body,
        href=f"/disputes/{dispute.dispute_id}",
    )
    try:
        send_mail(
            subject=f"[GrabIT] Dispute filed on order {order.order_id}",
            message=vendor_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.shop.owner.email],
        )
    except Exception as e:
        logger.error("Failed to send dispute_filed email to %s: %s", order.shop.owner.email, e)


@receiver(dispute_resolved)
def on_dispute_resolved(sender, dispute, **kwargs):
    order = dispute.order
    resolution_label = dispute.get_resolution_display()
    body = f"The dispute for order {order.order_id} has been resolved: {resolution_label}."

    for user in [order.buyer, order.shop.owner]:
        Notification.objects.create(
            user=user,
            type="dispute",
            title=f"Dispute {dispute.dispute_id} resolved",
            body=body,
            href=f"/disputes/{dispute.dispute_id}",
        )
        try:
            send_mail(
                subject=f"[GrabIT] Dispute {dispute.dispute_id} resolved",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
        except Exception as e:
            logger.error("Failed to send dispute_resolved email to %s: %s", user.email, e)
