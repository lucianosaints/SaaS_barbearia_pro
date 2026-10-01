from django.urls import path
from .views import MercadoPagoWebhookView, CriarPagamentoAssinaturaView

urlpatterns = [
    path('webhook/', MercadoPagoWebhookView.as_view(), name='webhook_mercadopago'),
    path('criar-assinatura/', CriarPagamentoAssinaturaView.as_view(), name='criar_assinatura'),
]
