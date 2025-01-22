# predictive/routing.py
from django.urls import path
from userside.tradovate_socket import TradovateConsumer

websocket_urlpatterns = [
    path('ws/tradovate/', TradovateConsumer.as_asgi()),
]