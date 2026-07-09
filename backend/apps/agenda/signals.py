from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from apps.agenda.models import Agendamento, FilaEspera
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Agendamento)
def enviar_confirmacao_agendamento(sender, instance: Agendamento, created: bool, **kwargs) -> None:
    """
    Escuta a criação de agendamentos e dispara um e-mail de confirmação para o cliente
    e uma notificação de WhatsApp para o barbeiro.
    """
    if not created:
        return

    cliente_nome = instance.cliente.get_full_name() or instance.cliente.username if instance.cliente else "Cliente"
    barbeiro_nome = instance.profissional.get_full_name() or instance.profissional.username if instance.profissional else "Barbeiro"
    data_formatada = instance.data_hora_inicio.strftime('%d/%m/%Y às %H:%M')
    
    # Constrói a listagem dos serviços
    servicos = instance.servicos.all()
    lista_servicos = ", ".join([s.nome for s in servicos]) if servicos.exists() else "Serviços contratados"

    if instance.cliente and instance.cliente.email:
        try:
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
            logger.error(f"Falha ao enviar e-mail de confirmação para agendamento {instance.id}: {str(e)}")

    # NOTIFICAÇÃO DO BARBEIRO VIA WAHA
    try:
        if instance.profissional and getattr(instance.profissional, 'telefone', None):
            from services.waha_service import enviar_mensagem_whatsapp
            msg_barbeiro = (
                f"💈 *Novo Agendamento!*\n\n"
                f"Você tem um novo horário marcado:\n"
                f"👤 Cliente: {cliente_nome}\n"
                f"📅 Data/Hora: {data_formatada}\n"
                f"✂️ Serviço(s): {lista_servicos}\n\n"
                f"Tenha um ótimo trabalho!"
            )
            enviar_mensagem_whatsapp(instance.profissional.telefone, msg_barbeiro)
    except Exception as e:
        logger.error(f"Falha ao enviar WAHA para agendamento {instance.id}: {str(e)}")


@receiver(pre_save, sender=Agendamento)
def calcular_valores_financeiros(sender, instance: Agendamento, **kwargs) -> None:
    """
    Signal pre_save para calcular comissão e lucro líquido quando o status
    muda para 'CONCLUIDO'. O valor_total já é preenchido pelo signal m2m_changed
    em models.py no momento da associação dos serviços.
    """
    if instance.status == 'CONCLUIDO' and instance.pk:
        # Se valor_total ainda não foi preenchido, tenta calcular agora
        if not instance.valor_total:
            total_servicos = sum(s.preco for s in instance.servicos.all())
            if total_servicos > 0:
                instance.valor_total = total_servicos

        # Calcula comissão e lucro líquido
        if instance.valor_total:
            taxa = 40.00
            if instance.profissional and hasattr(instance.profissional, 'taxa_comissao'):
                taxa = instance.profissional.taxa_comissao
            
            comissao = (instance.valor_total * taxa) / 100
            instance.valor_comissao = comissao
            instance.lucro_liquido = instance.valor_total - comissao


@receiver(post_save, sender=Agendamento)
def sniper_de_desistencias(sender, instance: Agendamento, created: bool, **kwargs) -> None:
    """
    Verifica se um agendamento foi cancelado. Se sim, procura na Fila de Espera 
    por alguém que queria esse horário e simula a notificação.
    """
    if instance.status == 'CANCELADO':
        data = instance.data_hora_inicio.date()
        horario = instance.data_hora_inicio.time()
        
        # Avisa o barbeiro sobre o cancelamento
        if instance.profissional and instance.profissional.telefone:
            from services.waha_service import enviar_mensagem_whatsapp
            cliente_nome = instance.cliente.get_full_name() or instance.cliente.username if instance.cliente else "Desconhecido"
            data_formatada = instance.data_hora_inicio.strftime('%d/%m/%Y às %H:%M')
            msg_barbeiro = (
                f"❌ *Agendamento Cancelado*\n\n"
                f"O cliente *{cliente_nome}* cancelou o horário de {data_formatada}.\n"
                f"O horário está livre agora."
            )
            enviar_mensagem_whatsapp(instance.profissional.telefone, msg_barbeiro)
            
        espera = FilaEspera.objects.filter(
            empresa=instance.empresa,
            data_desejada=data,
            horario_desejado=horario,
            notificado=False
        ).order_by('criado_em').first()
        
        if espera:
            espera.notificado = True
            espera.save()
            print(f"\n[SNIPER] Notificando {espera.cliente_nome} no WhatsApp {espera.cliente_telefone} sobre a vaga liberada!\n")
            logger.info(f"Notificando {espera.cliente_nome} ({espera.cliente_telefone}) sobre vaga liberada em {data} às {horario}.")
            
            # Notifica o cliente da fila de espera
            from services.waha_service import enviar_mensagem_whatsapp
            msg_fila = (
                f"Olá, {espera.cliente_nome}!\n\n"
                f"Uma vaga acabou de ser liberada na barbearia para o dia {data.strftime('%d/%m/%Y')} às {horario.strftime('%H:%M')}!\n"
                f"Acesse o app para agendar antes que outra pessoa pegue."
            )
            enviar_mensagem_whatsapp(espera.cliente_telefone, msg_fila)
