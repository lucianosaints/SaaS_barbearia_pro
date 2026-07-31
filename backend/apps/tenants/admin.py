from django.contrib import admin
from .models import Empresa

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug', 'cnpj', 'ativo', 'assinatura_ativa', 'data_vencimento_assinatura', 'em_trial')
    search_fields = ('nome', 'slug', 'cnpj')
