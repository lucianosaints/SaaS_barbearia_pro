from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario
from .admin_permissions import GlobalAdminOnly


class ClienteAtividadeFilter(admin.SimpleListFilter):
    title = 'clientes por atividade'
    parameter_name = 'cliente_atividade'

    def lookups(self, request, model_admin):
        return (
            ('ativos', 'Clientes ativos'),
            ('inativos', 'Clientes inativos'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'ativos':
            return queryset.filter(tipo='CLIENTE', is_active=True)
        if self.value() == 'inativos':
            return queryset.filter(tipo='CLIENTE', is_active=False)
        return queryset


@admin.register(Usuario)
class UsuarioAdmin(GlobalAdminOnly, UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo', 'empresa', 'is_active', 'is_staff')
    list_filter = (ClienteAtividadeFilter, 'tipo', 'is_staff', 'is_active', 'empresa')
    actions = ('desativar_clientes', 'reativar_clientes')
    fieldsets = UserAdmin.fieldsets + (
        ('Informações de Perfil', {'fields': ('tipo', 'telefone', 'empresa', 'foto', 'status', 'taxa_comissao', 'comissao_percentual', 'avaliacao')}),
        ('LGPD', {'fields': ('aceitou_termos', 'data_aceite_termos', 'ip_aceite_termos')}),
    )

    @admin.action(description='Desativar clientes selecionados (preserva o historico)')
    def desativar_clientes(self, request, queryset):
        clientes = queryset.filter(tipo='CLIENTE', is_active=True)
        atualizados = clientes.update(is_active=False, status='BLOQUEADO')
        self.message_user(
            request,
            f'{atualizados} cliente(s) desativado(s). O historico foi preservado.',
        )

    @admin.action(description='Reativar clientes selecionados')
    def reativar_clientes(self, request, queryset):
        clientes = queryset.filter(tipo='CLIENTE', is_active=False)
        atualizados = clientes.update(is_active=True, status='ATIVO')
        self.message_user(request, f'{atualizados} cliente(s) reativado(s).')
