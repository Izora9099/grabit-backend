from django.urls import path
from . import views

urlpatterns = [
    path("", views.OrderListCreateView.as_view(), name="orders"),
    # Static paths must come before dynamic <str:order_id>/ to avoid being swallowed
    path("messages/", views.MessageListCreateView.as_view(), name="messages"),
    path("agent/assignments/", views.AgentOrdersView.as_view(), name="agent-assignments"),
    path("agent/stats/", views.AgentStatsView.as_view(), name="agent-stats"),
    # Dynamic order routes
    path("<str:order_id>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("<str:order_id>/status/", views.OrderStatusUpdateView.as_view(), name="order-status"),
    path("<str:order_id>/confirm/", views.ConfirmDeliveryView.as_view(), name="order-confirm"),
    path("<str:order_id>/cancel/", views.OrderCancelView.as_view(), name="order-cancel"),
    path("<str:order_id>/decline/", views.AgentDeclineView.as_view(), name="order-agent-decline"),
]
