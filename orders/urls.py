from django.urls import path
from . import views

urlpatterns = [
    path("", views.OrderListCreateView.as_view(), name="orders"),
    # Public receipt verification — no auth required
    path("verify/<str:payment_id>/", views.PublicReceiptView.as_view(), name="order-verify"),
    # Static paths must come before dynamic <str:order_id>/ to avoid being swallowed
    path("messages/", views.MessageListCreateView.as_view(), name="messages"),
    path("messages/unread-count/", views.UnreadCountView.as_view(), name="messages-unread-count"),
    path("messages/conversations/", views.ConversationListView.as_view(), name="conversations"),
    path("messages/conversations/<int:user_id>/", views.ConversationDetailView.as_view(), name="conversation-detail"),
    path("messages/<int:pk>/", views.MessageMarkReadView.as_view(), name="message-mark-read"),
    path("agent/assignments/", views.AgentOrdersView.as_view(), name="agent-assignments"),
    path("agent/stats/", views.AgentStatsView.as_view(), name="agent-stats"),
    path("agent/earnings/", views.AgentEarningsView.as_view(), name="agent-earnings"),
    path("agent/payouts/", views.AgentPayoutsView.as_view(), name="agent-payouts"),
    path("agent/ratings/", views.AgentRatingsView.as_view(), name="agent-ratings"),
    path("agent/reconciliation/", views.AgentReconciliationView.as_view(), name="agent-reconciliation"),
    # Dynamic order routes
    path("<str:order_id>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("<str:order_id>/receipt/", views.OrderReceiptView.as_view(), name="order-receipt"),
    path("<str:order_id>/status/", views.OrderStatusUpdateView.as_view(), name="order-status"),
    path("<str:order_id>/confirm/", views.ConfirmDeliveryView.as_view(), name="order-confirm"),
    path("<str:order_id>/cancel/", views.OrderCancelView.as_view(), name="order-cancel"),
    path("<str:order_id>/decline/", views.AgentDeclineView.as_view(), name="order-agent-decline"),
    path("<str:order_id>/review/", views.DeliveryReviewCreateView.as_view(), name="order-delivery-review"),
]
