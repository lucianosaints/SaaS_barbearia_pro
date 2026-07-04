from datetime import timedelta
from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from apps.tenants.models import Empresa
from apps.accounts.models import Usuario

class Servico(models.Model):
    """
    Representa um serviço prestado na barbearia (ex: Corte de Cabelo, Barba).
    """
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="servicos",
        verbose_name=_("Empresa"),
        help_text=_("Empresa a qual o serviço pertence")
    )
    nome = models.CharField(
        max_length=150,
        verbose_name=_("Nome do Serviço")
    )
    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Preço")
    )
    duracao_minutos = models.PositiveIntegerField(
        verbose_name=_("Duração (Minutos)"),
        help_text=_("Tempo estimado em minutos para a execução do serviço")
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name=_("Ativo")
    )

    class Meta:
        verbose_name = _("Serviço")
        verbose_name_plural = _("Serviços")
        unique_together = ('empresa', 'nome')

    def __str__(self) -> str:
        return f"{self.nome} ({self.duracao_minutos} min) - R$ {self.preco}"


class Agendamento(models.Model):
    """
    Representa o agendamento de um ou mais serviços por um cliente
    com um profissional em uma data/hora específicas.
    """
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="agendamentos",
        verbose_name=_("Empresa")
    )
    cliente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="agendamentos_cliente",
        verbose_name=_("Cliente")
    )
    profissional = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="agendamentos_profissional",
        verbose_name=_("Profissional")
    )
    servicos = models.ManyToManyField(
        Servico,
        related_name="agendamentos",
        verbose_name=_("Serviços")
    )
    data_hora_inicio = models.DateTimeField(
        verbose_name=_("Data/Hora de Início")
    )
    data_hora_fim = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Data/Hora de Fim"),
        help_text=_("Calculado automaticamente somando a duração dos serviços selecionados")
    )
    STATUS_CHOICES = [
        ('PENDENTE', _('Pendente')),
        ('CONFIRMADO', _('Confirmado')),
        ('CONCLUIDO', _('Concluído')),
        ('CANCELADO', _('Cancelado')),
    ]
    STATUS_PAGAMENTO_CHOICES = [
        ('PENDENTE', _('Pendente')),
        ('PAGO', _('Pago')),
    ]
    METODO_PAGAMENTO_CHOICES = [
        ('PIX', _('Pix')),
        ('CARTAO', _('Cartão')),
        ('DINHEIRO', _('Dinheiro')),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDENTE',
        verbose_name=_("Status")
    )
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Observações")
    )
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Valor Total")
    )
    valor_comissao = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Valor da Comissão")
    )
    lucro_liquido = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Lucro Líquido")
    )
    status_pagamento = models.CharField(
        max_length=20,
        choices=STATUS_PAGAMENTO_CHOICES,
        default='PENDENTE',
        verbose_name=_("Status do Pagamento")
    )
    metodo_pagamento = models.CharField(
        max_length=20,
        choices=METODO_PAGAMENTO_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Método de Pagamento")
    )

    class Meta:
        verbose_name = _("Agendamento")
        verbose_name_plural = _("Agendamentos")
        ordering = ['data_hora_inicio']

    def __str__(self) -> str:
        return f"{self.cliente} com {self.profissional} em {self.data_hora_inicio.strftime('%d/%m/%Y %H:%M')}"

    def recalcular_fim(self) -> None:
        """
        Calcula a data e hora do fim do agendamento com base na soma da duração
        de todos os serviços selecionados.
        """
        if not self.pk:
            # Não é possível calcular antes de salvar o objeto no banco
            # para obter o relacionamento ManyToMany.
            return
        
        total_duracao = sum(servico.duracao_minutos for servico in self.servicos.all())
        self.data_hora_fim = self.data_hora_inicio + timedelta(minutes=total_duracao)


@receiver(m2m_changed, sender=Agendamento.servicos.through)
def atualizar_data_hora_fim(sender, instance: Agendamento, action: str, **kwargs) -> None:
    """
    Signal para escutar alterações no relacionamento ManyToMany de serviços do Agendamento.
    Atualiza e salva o campo `data_hora_fim` e calcula o `valor_total` automaticamente.
    """
    if action in ["post_add", "post_remove", "post_clear"]:
        servicos = instance.servicos.all()
        
        # Recalcula data_hora_fim
        total_duracao = sum(servico.duracao_minutos for servico in servicos)
        instance.data_hora_fim = instance.data_hora_inicio + timedelta(minutes=total_duracao)
        
        # Calcula valor_total baseado nos serviços associados
        valor_total = sum(servico.preco for servico in servicos)
        instance.valor_total = valor_total
        
        # Salva apenas os campos atualizados para evitar recursão ou triggers desnecessários
        instance.save(update_fields=["data_hora_fim", "valor_total"])
