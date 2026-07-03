from django.urls import path
from .views import MercadoPagoWebhookView

urlpatterns = [
    path('webhook/', MercadoPagoWebhookView.as_view(), name='webhook_mercadopago'),
]
