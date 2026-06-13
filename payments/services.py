import requests
from django.conf import settings
from django.db import transaction

from orders.models import EscrowEvent, Order
from orders.signals import payment_confirmed
from .models import Payment


class FapshiError(Exception):
    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class FapshiCollectionService:
    """Thin wrapper around Fapshi's collection endpoints."""

    def __init__(self):
        self.base_url = settings.FAPSHI_BASE_URL.rstrip("/")
        self.headers = {
            "apiuser": settings.FAPSHI_API_USER,
            "apikey": settings.FAPSHI_API_KEY,
            "Content-Type": "application/json",
        }
        self.timeout = 30

    def direct_pay(self, *, amount, phone, external_id, medium=None,
                   name=None, email=None, user_id=None, message=None):
        if int(amount) < 100:
            raise FapshiError("Amount must be at least 100 XAF.")
        body = {"amount": int(amount), "phone": phone, "externalId": external_id}
        if medium:   body["medium"] = medium
        if name:     body["name"] = name
        if email:    body["email"] = email
        if user_id:  body["userId"] = user_id
        if message:  body["message"] = message
        data = self._request("POST", "/direct-pay", json=body)
        return data["transId"]

    def get_status(self, trans_id):
        return self._request("GET", f"/payment-status/{trans_id}")

    def _request(self, method, path, json=None):
        try:
            r = requests.request(
                method, self.base_url + path,
                json=json, headers=self.headers, timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise FapshiError(f"Network error calling Fapshi: {e}")
        try:
            data = r.json()
        except ValueError:
            data = {}
        if r.status_code != 200:
            raise FapshiError(
                data.get("message", "Fapshi request failed"),
                r.status_code, data,
            )
        return data


def settle_payment_from_status(trans_id, txn):
    """
    Apply a VERIFIED Fapshi transaction dict to our Payment + Order.
    Called by both the webhook and the reconciliation task.

    Idempotent: row lock + status guards ensure replaying the same event
    never double-applies, never creates a duplicate EscrowEvent, and never
    double-fires the signal.  `txn` is the body from GET /payment-status.
    """
    api_status = txn.get("status")

    if api_status == "SUCCESSFUL":
        fire_confirmed = False
        with transaction.atomic():
            try:
                payment = Payment.objects.select_for_update().get(external_ref=trans_id)
            except Payment.DoesNotExist:
                return
            order = Order.objects.select_for_update().get(pk=payment.order_id)

            # Amount integrity: buyer must have paid at least the order total.
            if int(txn.get("amount", 0)) < order.total:
                return  # underpayment — leave for manual review

            if payment.status != "paid":
                payment.status = "paid"
                payment.save(update_fields=["status"])

            if order.status == "awaiting_payment":
                order.status = "paid_escrow"
                order.save(update_fields=["status"])
                EscrowEvent.objects.create(
                    order=order,
                    event="held",
                    amount=order.total,
                    note="Payment verified via Fapshi. Funds held in escrow.",
                )
                fire_confirmed = True

        # Fire AFTER commit so notification receivers see committed state.
        if fire_confirmed:
            payment_confirmed.send(sender=Payment, payment=payment, order=order)

    elif api_status == "FAILED":
        with transaction.atomic():
            try:
                payment = Payment.objects.select_for_update().get(external_ref=trans_id)
            except Payment.DoesNotExist:
                return
            if payment.status != "paid":
                payment.status = "failed"
                payment.save(update_fields=["status"])

    # EXPIRED / CREATED / PENDING: no-op.
