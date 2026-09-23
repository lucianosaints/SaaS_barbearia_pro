import uuid

from django.db import models


class CobrancaAssinatura(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADA', 'Aprovada'),
        ('REJEITADA', 'Rejeitada'),
        ('ERRO', 'Erro'),
    ]

    empresa = models.ForeignKey('tenants.Empresa', on_delete=models.PROTECT, related_name='cobrancas_assinatura')
    external_reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    meses = models.PositiveSmallIntegerField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    moeda = models.CharField(max_length=3, default='BRL')
    mercado_pago_payment_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDENTE')
    criada_em = models.DateTimeField(auto_now_add=True)
    processada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-criada_em']
