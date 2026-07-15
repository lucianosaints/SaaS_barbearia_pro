from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from django.views.static import serve
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

# Importando as ViewSets e views customizadas
from apps.tenants.views import EmpresaViewSet
from apps.accounts.views import UsuarioViewSet, registrar_cliente, registrar_saas, CustomTokenObtainPairView
from apps.agenda.views import ServicoViewSet, AgendamentoViewSet, obter_disponibilidade, FinancasDashboardView, ComissoesView, MeuCartaoFidelidadeView, BloqueioHorarioViewSet, FilaEsperaViewSet
from apps.tenants.waha_views import WahaQRCodeView

# Inicializando o roteador principal do DRF
router = DefaultRouter()
router.register(r'empresas', EmpresaViewSet, basename='empresa')
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'servicos', ServicoViewSet, basename='servico')
router.register(r'agendamentos', AgendamentoViewSet, basename='agendamento')
router.register(r'bloqueios', BloqueioHorarioViewSet, basename='bloqueio')
router.register(r'fila-espera', FilaEsperaViewSet, basename='fila_espera')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Endpoint customizado de disponibilidade
    path('api/disponibilidade/', obter_disponibilidade, name='obter_disponibilidade'),
    
    # Endpoint consolidado financeiro do Dashboard
    path('api/financas/dashboard/', FinancasDashboardView.as_view(), name='financas_dashboard'),
    
    # Endpoint de comissões isolado
    path('api/financeiro/comissoes/', ComissoesView.as_view(), name='financeiro_comissoes'),
    
    # Endpoint do Cartão Fidelidade
    path('api/fidelidade/meu-cartao/', MeuCartaoFidelidadeView.as_view(), name='meu_cartao_fidelidade'),
    
    # Endpoint do WhatsApp QR Code com regex para aceitar parâmetro dinâmico de cache buster
    re_path(r'^api/whatsapp/qrcode/(?:(?P<cache_buster>[^/]+)/)?$', WahaQRCodeView.as_view(), name='whatsapp_qrcode'),
    
    # Endpoint de registro de cliente
    path('api/clientes/registrar/', registrar_cliente, name='registrar_cliente'),
    
    # Endpoint de registro de SaaS
    path('api/saas/registrar/', registrar_saas, name='registrar_saas'),
    
    # Endpoints da API REST
    path('api/assinaturas/', include('apps.payments.urls')),
    path('api/', include(router.urls)),
    
    # Endpoints de Autenticação (JWT)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Em produção, garante que a rota de media funcione via Gunicorn/Django
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
