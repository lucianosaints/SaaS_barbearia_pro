from django.contrib import admin
from .models import Servico, Agendamento
from apps.accounts.admin_permissions import GlobalAdminOnly

@admin.register(Servico)
class ServicoAdmin(GlobalAdminOnly, admin.ModelAdmin):
    list_display = ('nome', 'empresa', 'preco', 'duracao_minutos', 'ativo')
    list_filter = ('empresa', 'ativo')
    search_fields = ('nome',)

@admin.register(Agendamento)
class AgendamentoAdmin(GlobalAdminOnly, admin.ModelAdmin):
    list_display = ('cliente', 'profissional', 'data_hora_inicio', 'data_hora_fim', 'status', 'empresa')
    list_filter = ('status', 'empresa', 'profissional')
    search_fields = ('cliente__username', 'profissional__username')

    # A reserva passa pela API transacional; o admin permanece disponível para consulta.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
