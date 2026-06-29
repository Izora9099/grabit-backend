import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

# get_asgi_application() must be called before any models are imported so that
# Django's app registry is ready before Channels imports consumers.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter          # noqa: E402
from tracking.middleware import JWTAuthMiddleware                    # noqa: E402
from tracking.routing import websocket_urlpatterns as tracking_patterns  # noqa: E402
from orders.routing import websocket_urlpatterns as chat_patterns    # noqa: E402

all_websocket_patterns = tracking_patterns + chat_patterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(all_websocket_patterns)
    ),
})
