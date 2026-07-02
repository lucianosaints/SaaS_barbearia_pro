from django.db import models
from django.utils.translation import gettext_lazy as _

class Empresa(models.Model):
    """
    Representa a empresa/barbearia (Tenant).
    Todos os dados do sistema devem estar associados a este modelo para garantir
    o isolamento de dados do SaaS.
    """
    nome = models.CharField(
        max_length=255, 
        verbose_name=_("Nome da Empresa"),
        help_text=_("Nome fantasia da barbearia")
    )
    slug = models.SlugField(
        unique=True, 
        max_length=100,
        verbose_name=_("Identificador Único (Slug)"),
        help_text=_("Usado para subdomínios ou rotas na URL da barbearia")
    )
    cnpj = models.CharField(
        max_length=14, 
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("CNPJ")
    )
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Data de Criação")
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name=_("Ativo"),
        help_text=_("Indica se a empresa está ativa no SaaS")
    )
    hora_abertura = models.TimeField(
        default='09:00:00',
        verbose_name=_("Horário de Abertura")
    )
    hora_fechamento = models.TimeField(
        default='19:00:00',
        verbose_name=_("Horário de Fechamento")
    )
    intervalo_almoco_inicio = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Início do Intervalo de Almoço")
    )
    intervalo_almoco_fim = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Fim do Intervalo de Almoço")
    )

    class Meta:
        verbose_name = _("Empresa")
        verbose_name_plural = _("Empresas")
        ordering = ['nome']

    def __str__(self) -> str:
        return self.nome
