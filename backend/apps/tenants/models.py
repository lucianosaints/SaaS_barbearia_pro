from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

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
        blank=True,
        null=True,
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
    assinatura_ativa = models.BooleanField(
        default=False,
        verbose_name=_("Assinatura Ativa"),
        help_text=_("Indica se a barbearia possui uma assinatura paga e ativa.")
    )
    em_trial = models.BooleanField(
        default=True,
        verbose_name=_("Em Período de Teste"),
        help_text=_("Indica se a barbearia ainda está no Free Trial.")
    )
    data_fim_trial = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Fim do Período de Teste"),
        help_text=_("Data em que o período de teste expira.")
    )
    dias_retorno_lembrete = models.IntegerField(
        default=25, 
        verbose_name=_("Dias para lembrete de retorno"),
        help_text=_("Quantidade de dias após o último serviço para enviar o lembrete automático via WhatsApp.")
    )
    fidelidade_ativo = models.BooleanField(
        default=True,
        verbose_name=_("Programa de Fidelidade Ativo"),
        help_text=_("Ativa ou desativa o cartão fidelidade digital para os clientes.")
    )
    exigir_sinal = models.BooleanField(
        default=False,
        verbose_name=_("Exigir Sinal (50%)"),
        help_text=_("Exige confirmação via PIX de 50% do valor do serviço.")
    )
    chave_pix = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name=_("Chave PIX"),
        help_text=_("Chave PIX para recebimento do sinal.")
    )
    beneficiario_pix = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name=_("Beneficiário do PIX"),
        help_text=_("Nome da pessoa ou empresa que receberá o PIX.")
    )
    horas_limite_cancelamento = models.PositiveIntegerField(
        default=24,
        verbose_name=_("Horas Limite para Cancelamento Automático"),
        help_text=_("Impede que o cliente cancele sozinho se faltar menos que X horas para o serviço.")
    )
    fidelidade_meta = models.IntegerField(
        default=10,
        verbose_name=_("Meta de Selos"),
        help_text=_("Quantidade de selos necessários para o cliente ganhar o prêmio.")
    )
    ESTILOS_FIDELIDADE = [
        ('estrela', 'Estrela (Elegante / Unissex)'),
        ('cuidado', 'Cuidado (Feminino / Delicado)'),
        ('classic', 'Clássico (Neutro / Universal)'),
        ('goku', 'Goku (Legado)') # Mantido para não quebrar compatibilidade
    ]
    fidelidade_estilo = models.CharField(
        max_length=50,
        choices=ESTILOS_FIDELIDADE,
        default='estrela',
        verbose_name=_("Estilo Visual do Cartão"),
        help_text=_("Tema visual que será renderizado no painel do cliente.")
    )

    class Meta:
        verbose_name = _("Empresa")
        verbose_name_plural = _("Empresas")
        ordering = ['nome']

    def __str__(self) -> str:
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug and self.nome:
            base_slug = slugify(self.nome)
            slug = base_slug
            counter = 1
            while Empresa.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
