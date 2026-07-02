from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from apps.tenants.models import Empresa

class Usuario(AbstractUser):
    """
    Modelo de usuário customizado estendido a partir do AbstractUser do Django.
    Incorpora o isolamento de dados de empresa (multi-tenant) e campos de
    consentimento exigidos pela LGPD.
    """
    TIPO_CHOICES = [
        ('CLIENTE', _('Cliente')),
        ('PROFISSIONAL', _('Profissional')),
        ('ADMINISTRADOR', _('Administrador')),
    ]
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='CLIENTE',
        verbose_name=_("Tipo de Usuário")
    )
    telefone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_("Telefone")
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="usuarios",
        verbose_name=_("Empresa"),
        help_text=_("A barbearia à qual este usuário pertence. Pode ser nulo para administradores globais do SaaS.")
    )
    taxa_comissao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=40.00,
        verbose_name=_("Taxa de Comissão"),
        help_text=_("Percentual de comissão individual do profissional (ex: 40.0)")
    )

    # Campos de Auditoria LGPD
    aceitou_termos = models.BooleanField(
        default=False,
        verbose_name=_("Aceitou Termos de Uso"),
        help_text=_("Indica se o usuário concordou com os termos e políticas da plataforma.")
    )
    data_aceite_termos = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Data e Hora do Aceite"),
        help_text=_("Data e hora exata em que o aceite dos termos foi registrado.")
    )
    ip_aceite_termos = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP de Origem do Aceite"),
        help_text=_("Endereço IP utilizado pelo usuário ao aceitar os termos.")
    )

    class Meta:
        verbose_name = _("Usuário")
        verbose_name_plural = _("Usuários")

    def __str__(self) -> str:
        if self.empresa:
            return f"{self.get_full_name() or self.username} ({self.empresa.nome})"
        return f"{self.get_full_name() or self.username} [Global]"
