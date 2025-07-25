# project/asgi.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Lenzly.settings')
django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import chat_system.routing

from chat_system.routing import websocket_urlpatterns
from chat_system.middleware import JWTAuthMiddleware


application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    # 'websocket': AuthMiddlewareStack(
    #     URLRouter(chat_system.routing.websocket_urlpatterns)
    # ),
    "websocket": JWTAuthMiddleware(  # ƏVVƏLKİ AuthMiddlewareStack yerinə
        URLRouter(websocket_urlpatterns)
    ),
})
