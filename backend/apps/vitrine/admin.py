from django.contrib import admin

from .models import Produto


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'empresa', 'preco', 'preco_promocional', 'estoque', 'disponivel', 'destaque')
    list_filter = ('empresa', 'disponivel', 'destaque')
    search_fields = ('nome', 'empresa__nome')
