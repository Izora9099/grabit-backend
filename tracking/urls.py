from django.urls import path
from .views import AgentLocationView

urlpatterns = [
    path("<str:order_id>/location/", AgentLocationView.as_view(), name="agent-location"),
]
