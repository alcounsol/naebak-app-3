"""
تكوين ASGI لمشروع نائبك دوت كوم
يدعم WebSockets عبر Django Channels
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# تحديد إعدادات Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# تهيئة Django ASGI application
django_asgi_app = get_asgi_application()

# استيراد routing للـ WebSockets (سيتم إنشاؤه لاحقاً)
try:
    from naebak.routing import websocket_urlpatterns
except ImportError:
    websocket_urlpatterns = []

application = ProtocolTypeRouter({
    # HTTP requests
    "http": django_asgi_app,
    
    # WebSocket requests
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
