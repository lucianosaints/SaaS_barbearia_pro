from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

# Importando as ViewSets e views customizadas
from apps.tenants.views import EmpresaViewSet
from apps.accounts.views import UsuarioViewSet, registrar_cliente, CustomTokenObtainPairView
from apps.agenda.views import ServicoViewSet, AgendamentoViewSet, obter_disponibilidade, FinancasDashboardView

# Inicializando o roteador principal do DRF
router = DefaultRouter()
router.register(r'empresas', EmpresaViewSet, basename='empresa')
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'servicos', ServicoViewSet, basename='servico')
router.register(r'agendamentos', AgendamentoViewSet, basename='agendamento')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Endpoint customizado de disponibilidade
    path('api/disponibilidade/', obter_disponibilidade, name='obter_disponibilidade'),
    
    # Endpoint consolidado financeiro do Dashboard
    path('api/financas/dashboard/', FinancasDashboardView.as_view(), name='financas_dashboard'),
    
    # Endpoint de registro de cliente
    path('api/clientes/registrar/', registrar_cliente, name='registrar_cliente'),
    
    # Endpoints da API REST
    path('api/', include(router.urls)),
    
    # Endpoints de Autenticação (JWT)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
