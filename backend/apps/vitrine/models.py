from django.core.validators import MinValueValidator
from django.db import models

from apps.tenants.models import Empresa


class Produto(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='produtos')
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, default='')
    preco = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    preco_promocional = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    estoque = models.PositiveIntegerField(default=0)
    controlar_estoque = models.BooleanField(default=True)
    disponivel = models.BooleanField(default=True)
    destaque = models.BooleanField(default=False)
    foto = models.ImageField(upload_to='produtos/', blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-destaque', 'nome']
        constraints = [
            models.UniqueConstraint(fields=['empresa', 'nome'], name='produto_nome_unico_por_empresa'),
        ]

    @property
    def em_estoque(self):
        return not self.controlar_estoque or self.estoque > 0

    @property
    def preco_atual(self):
        return self.preco_promocional if self.preco_promocional is not None else self.preco

    def __str__(self):
        return f'{self.nome} - {self.empresa.nome}'
