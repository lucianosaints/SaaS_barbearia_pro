from django.contrib import admin
from .models import Servico, Agendamento

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'empresa', 'preco', 'duracao_minutos', 'ativo')
    list_filter = ('empresa', 'ativo')
    search_fields = ('nome',)

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'profissional', 'data_hora_inicio', 'data_hora_fim', 'status', 'empresa')
    list_filter = ('status', 'empresa', 'profissional')
    search_fields = ('cliente__username', 'profissional__username')
