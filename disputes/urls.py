from django.urls import path
from . import views

urlpatterns = [
    path("", views.DisputeListCreateView.as_view(), name="disputes"),
    path("<str:dispute_id>/", views.DisputeDetailView.as_view(), name="dispute-detail"),
    path("<str:dispute_id>/resolve/", views.ResolveDisputeView.as_view(), name="dispute-resolve"),
]
