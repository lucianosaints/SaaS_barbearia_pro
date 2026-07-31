from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo', 'empresa', 'is_staff')
    list_filter = ('tipo', 'is_staff', 'is_active', 'empresa')
    fieldsets = UserAdmin.fieldsets + (
        ('Informações de Perfil', {'fields': ('tipo', 'telefone', 'empresa', 'foto', 'status', 'taxa_comissao', 'comissao_percentual', 'avaliacao')}),
        ('LGPD', {'fields': ('aceitou_termos', 'data_aceite_termos', 'ip_aceite_termos')}),
    )
