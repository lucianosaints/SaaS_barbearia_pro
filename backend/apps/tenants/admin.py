from django.contrib import admin
from .models import Empresa
from apps.accounts.admin_permissions import GlobalAdminOnly

@admin.register(Empresa)
class EmpresaAdmin(GlobalAdminOnly, admin.ModelAdmin):
    list_display = ('nome', 'slug', 'cnpj', 'ativo', 'hora_abertura', 'hora_fechamento')
    search_fields = ('nome', 'slug', 'cnpj')
