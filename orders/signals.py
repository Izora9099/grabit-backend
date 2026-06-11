from django.dispatch import Signal

# Fired when an order's status changes.
# kwargs: order (Order), old_status (str), new_status (str), actor (User)
order_status_changed = Signal()

# Fired when a payment is confirmed and escrow is funded.
# kwargs: payment (Payment), order (Order)
payment_confirmed = Signal()

# Fired when a dispute is filed.
# kwargs: dispute (Dispute)
dispute_filed = Signal()

# Fired when a dispute is resolved by admin.
# kwargs: dispute (Dispute)
dispute_resolved = Signal()
