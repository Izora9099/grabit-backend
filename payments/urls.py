from django.urls import path
from . import views

urlpatterns = [
    path("initiate/", views.InitiatePaymentView.as_view(), name="payment-initiate"),
    path("payouts/", views.PayoutListView.as_view(), name="payouts"),
]
