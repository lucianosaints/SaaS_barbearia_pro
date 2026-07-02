from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from apps.agenda.models import Agendamento
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Agendamento)
def enviar_confirmacao_agendamento(sender, instance: Agendamento, created: bool, **kwargs) -> None:
    """
    Escuta a criação de agendamentos e dispara um e-mail de confirmação para o cliente.
    Embrulhado em bloco try-except para evitar que falhas de email interrompam o fluxo principal.
    """
    if not created:
        return

    # Garante que as relações essenciais existem e o cliente tem e-mail
    if not instance.cliente or not instance.cliente.email:
        return

    try:
        cliente_nome = instance.cliente.get_full_name() or instance.cliente.username
        barbeiro_nome = instance.profissional.get_full_name() or instance.profissional.username
        data_formatada = instance.data_hora_inicio.strftime('%d/%m/%Y às %H:%M')
        
        # Constrói a listagem dos serviços
        servicos = instance.servicos.all()
        lista_servicos = ", ".join([s.nome for s in servicos]) if servicos.exists() else "Serviços contratados"

        assunto = f"Confirmação de Agendamento - Golden Barber"
        corpo_mensagem = (
            f"Olá, {cliente_nome}!\n\n"
            f"Seu agendamento na Golden Barber foi registrado com sucesso!\n\n"
            f"Detalhes do seu horário:\n"
            f"- Profissional: {barbeiro_nome}\n"
            f"- Serviços: {lista_servicos}\n"
            f"- Data e Horário: {data_formatada}\n\n"
            f"Caso precise remarcar ou cancelar, entre em contato conosco ou acesse nosso app.\n"
            f"Agradecemos a preferência!"
        )

        send_mail(
            subject=assunto,
            message=corpo_mensagem,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.cliente.email],
            fail_silently=False,
        )
        logger.info(f"E-mail de confirmação enviado para {instance.cliente.email} referente ao agendamento {instance.id}.")
    except Exception as e:
        # Registra o log do erro para diagnóstico sem travar a requisição HTTP de agendamento (erro 500)
        logger.error(f"Falha ao enviar e-mail de confirmação para agendamento {instance.id}: {str(e)}")
