from django.urls import path
from . import views

urlpatterns = [
    path("initiate/", views.InitiatePaymentView.as_view(), name="payment-initiate"),
    path("payouts/", views.PayoutListView.as_view(), name="payouts"),
    path("balance/", views.VendorBalanceView.as_view(), name="vendor-balance"),
    path("payout-request/", views.PayoutRequestView.as_view(), name="payout-request"),
    path("webhook/fapshi/", views.FapshiWebhookView.as_view(), name="fapshi-webhook"),
    path("platform-config/", views.PlatformConfigView.as_view(), name="platform-config"),
]
