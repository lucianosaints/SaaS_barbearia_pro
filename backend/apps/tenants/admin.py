from django.contrib import admin
from .models import Empresa

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug', 'cnpj', 'ativo', 'hora_abertura', 'hora_fechamento')
    search_fields = ('nome', 'slug', 'cnpj')
