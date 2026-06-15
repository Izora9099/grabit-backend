from django.urls import path
from . import views

urlpatterns = [
    path("initiate/", views.InitiatePaymentView.as_view(), name="payment-initiate"),
    path("payouts/", views.PayoutListView.as_view(), name="payouts"),
    path("webhook/fapshi/", views.FapshiWebhookView.as_view(), name="fapshi-webhook"),
    path("fapshi-ping/", views.FapshiPingView.as_view(), name="fapshi-ping"),
]
