from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from apps.agenda.models import Agendamento, FilaEspera
from apps.agenda.background import enqueue_notification
import logging

logger = logging.getLogger(__name__)


def _dispatch_notification(callback) -> None:
    if settings.AGENDA_NOTIFICATIONS_ASYNC:
        enqueue_notification(callback)
    else:
        callback()

@receiver(post_save, sender=Agendamento)
def marcar_agendamento_criado(sender, instance: Agendamento, created: bool, **kwargs) -> None:
    if created:
        instance._just_created = True

@receiver(m2m_changed, sender=Agendamento.servicos.through)
def enviar_confirmacao_agendamento(sender, instance: Agendamento, action: str, **kwargs) -> None:
    """
    Escuta a adição de serviços ao agendamento recém-criado e dispara um e-mail de confirmação para o cliente
    e uma notificação de WhatsApp para o barbeiro.
    """
    if action == "post_add" and getattr(instance, '_just_created', False):
        # Previne disparos duplicados na mesma instância
        instance._just_created = False

        def disparar_notificacoes():
            # Busca a instância atualizada para ter acesso correto aos campos ManyToMany
            inst = Agendamento.objects.get(pk=instance.pk)
            
            cliente_nome = inst.cliente.get_full_name() or inst.cliente.username if inst.cliente else "Cliente"
            barbeiro_nome = inst.profissional.get_full_name() or inst.profissional.username if inst.profissional else "Profissional"
            # Formata a data para o fuso do Brasil usando biblioteca nativa do Python
            from zoneinfo import ZoneInfo
            fuso_local = ZoneInfo('America/Sao_Paulo')
            datetime_local = inst.data_hora_inicio.astimezone(fuso_local)
            data_formatada = datetime_local.strftime('%d/%m/%Y às %H:%M')
            
            # Constrói a listagem dos serviços
            servicos = inst.servicos.all()
            lista_servicos = ", ".join([s.nome for s in servicos]) if servicos.exists() else "Serviços contratados"
            
            # Forma de pagamento
            forma_pagamento = inst.get_metodo_pagamento_display() or "Não informado"

            if inst.cliente and inst.cliente.email:
                try:
                    nome_salao = inst.empresa.nome if inst.empresa else "Salão Pro"
                    assunto = f"Confirmação de Agendamento - {nome_salao}"
                    corpo_mensagem = (
                        f"Olá, {cliente_nome}!\n\n"
                        f"Seu agendamento no {nome_salao} foi registrado com sucesso!\n\n"
                        f"Detalhes do seu horário:\n"
                        f"- Profissional: {barbeiro_nome}\n"
                        f"- Serviços: {lista_servicos}\n"
                        f"- Pagamento: {forma_pagamento}\n"
                        f"- Data e Horário: {data_formatada}\n\n"
                        f"Caso precise remarcar ou cancelar, entre em contato conosco ou acesse nosso app.\n"
                        f"Agradecemos a preferência!"
                    )

                    send_mail(
                        subject=assunto,
                        message=corpo_mensagem,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[inst.cliente.email],
                        fail_silently=False,
                    )
                    logger.info(f"E-mail de confirmação enviado para {inst.cliente.email} referente ao agendamento {inst.id}.")
                except Exception as e:
                    logger.error(f"Falha ao enviar e-mail de confirmação para agendamento {inst.id}: {str(e)}")

            # NOTIFICAÇÃO DO SALÃO VIA WAHA
            try:
                if inst.empresa:
                    from services.waha_service import enviar_mensagem_whatsapp
                    from apps.accounts.models import Usuario
                    
                    import re
                    cliente_telefone_raw = getattr(inst.cliente, 'telefone', '') if inst.cliente else ''
                    numero_limpo = re.sub(r'\D', '', str(cliente_telefone_raw))
                    
                    telefone_formatado = "Não informado"
                    link_wa = ""
                    
                    if numero_limpo:
                        num_sem_ddi = numero_limpo[2:] if numero_limpo.startswith('55') else numero_limpo
                        if len(num_sem_ddi) >= 10:
                            ddd = num_sem_ddi[:2]
                            resto = num_sem_ddi[2:]
                            if len(resto) == 9:
                                telefone_formatado = f"({ddd}) {resto[:5]}-{resto[5:]}"
                            else:
                                telefone_formatado = f"({ddd}) {resto[:4]}-{resto[4:]}"
                        else:
                            telefone_formatado = cliente_telefone_raw
                        
                        numero_link = numero_limpo if numero_limpo.startswith('55') else f"55{numero_limpo}"
                        link_wa = f"https://wa.me/{numero_link}"
                    
                    nome_salao = inst.empresa.nome if inst.empresa else "Salão Pro"
                    msg_barbeiro = (
                        f"💈 *Novo Agendamento no {nome_salao}!*\n\n"
                        f"Você tem um novo horário marcado:\n"
                        f"👤 Cliente: {cliente_nome}\n"
                    )
                    
                    if link_wa:
                        msg_barbeiro += f"📞 WhatsApp: {telefone_formatado}\n"
                        
                    msg_barbeiro += (
                        f"📅 Data/Hora: {data_formatada}\n"
                        f"✂️ Serviço(s): {lista_servicos}\n"
                        f"💳 Forma de Pagamento: {forma_pagamento}\n\n"
                    )
                    
                    if link_wa:
                        msg_barbeiro += f"💬 Falar com o cliente: {link_wa}\n\n"
                        
                    msg_barbeiro += "Tenha um ótimo trabalho!"

                    destinatarios = []
                    if inst.profissional and getattr(inst.profissional, 'telefone', None):
                        destinatarios.append(inst.profissional.telefone)
                    destinatarios.extend(
                        Usuario.objects.filter(
                            empresa=inst.empresa,
                            tipo='ADMINISTRADOR',
                            is_active=True,
                        ).exclude(telefone__isnull=True).exclude(telefone='').values_list('telefone', flat=True)
                    )

                    session_id = f"tenant_{inst.empresa.id}"
                    numeros_enviados = set()
                    for telefone in destinatarios:
                        numero_normalizado = re.sub(r'\D', '', str(telefone))
                        if not numero_normalizado or numero_normalizado in numeros_enviados:
                            continue
                        numeros_enviados.add(numero_normalizado)
                        enviar_mensagem_whatsapp(telefone, msg_barbeiro, waha_session=session_id)
            except Exception as e:
                logger.error(f"Falha ao enviar WAHA para agendamento {inst.id}: {str(e)}")

            # NOTIFICAÇÃO DO CLIENTE VIA WAHA
            try:
                if inst.cliente and getattr(inst.cliente, 'telefone', None):
                    from services.waha_service import enviar_mensagem_whatsapp
                    
                    nome_salao = inst.empresa.nome if inst.empresa else "Salão Pro"
                    msg_cliente = (
                        f"Olá, {cliente_nome}!\n\n"
                        f"Seu agendamento no *{nome_salao}* foi registrado!\n\n"
                        f"💈 *Detalhes do seu horário:*\n"
                        f"👤 Profissional: {barbeiro_nome}\n"
                        f"📅 Data/Hora: {data_formatada}\n"
                        f"✂️ Serviço(s): {lista_servicos}\n"
                        f"💳 Forma de Pagamento: {forma_pagamento}\n"
                    )

                    empresa = inst.empresa
                    cliente_exige_sinal = (inst.cliente and getattr(inst.cliente, 'status', 'ATIVO') == 'EXIGIR_SINAL')
                    empresa_exige_sinal = getattr(empresa, 'exigir_sinal', False)
                    
                    if empresa and (empresa_exige_sinal or cliente_exige_sinal) and getattr(empresa, 'chave_pix', ''):
                        total_servicos = sum(s.preco for s in inst.servicos.all())
                        valor_sinal = total_servicos / 2
                        chave = empresa.chave_pix
                        beneficiario = getattr(empresa, 'beneficiario_pix', '')
                        horas_limite_cancelamento = getattr(empresa, 'horas_limite_cancelamento', 24)
                        
                        msg_cliente += (
                            f"\n✨ *SEU HORÁRIO ESTÁ RESERVADO ESPECIALMENTE PARA VOCÊ*\n"
                            f"Para confirmarmos essa reserva e mantermos esse período dedicado exclusivamente ao seu atendimento, "
                            f"solicitamos um sinal de 50% do valor do serviço via PIX.\n\n"
                            f"💰 *Valor do Sinal:* R$ {valor_sinal:.2f}\n"
                            f"🔑 *Chave PIX:* `{chave}`\n"
                        )
                        if beneficiario:
                            msg_cliente += f"👤 *Beneficiário:* {beneficiario}\n"
                        
                        msg_cliente += (
                            f"\nPor gentileza, envie o comprovante em até *15 minutos*. Assim, seu horário ficará confirmado e reservado para você.\n"
                            f"ℹ️ Como esse período é separado especialmente para o seu atendimento, em caso de cancelamento com menos de "
                            f"{horas_limite_cancelamento}h de antecedência, o sinal não será reembolsável.\n"
                            f"Agradecemos a confiança e esperamos por você! 😊"
                        )
                    else:
                        msg_cliente += f"\nCaso precise remarcar ou cancelar, acesse nosso app.\n"
                        msg_cliente += f"Agradecemos a preferência!"

                    session_id = f"tenant_{inst.empresa.id}" if inst.empresa else 'default'
                    enviar_mensagem_whatsapp(inst.cliente.telefone, msg_cliente, waha_session=session_id)
            except Exception as e:
                logger.error(f"Falha ao enviar WAHA para cliente no agendamento {inst.id}: {str(e)}")

        from django.db import transaction
        # O WAHA pode aguardar até 10 segundos por destinatário. Executar essas
        # chamadas no on_commit atrasa a resposta HTTP e faz o navegador acusar
        # timeout mesmo depois de a reserva ter sido salva com sucesso.
        transaction.on_commit(lambda: _dispatch_notification(disparar_notificacoes))


@receiver(pre_save, sender=Agendamento)
def calcular_valores_financeiros(sender, instance, **kwargs):
    from decimal import Decimal, ROUND_HALF_UP
    previous = Agendamento.objects.filter(pk=instance.pk).values_list('status', flat=True).first() if instance.pk else None
    instance._previous_status = previous
    if instance.status == 'CONCLUIDO' and previous != 'CONCLUIDO' and instance.pk:
        total = instance.valor_total
        if total is None:
            total = sum((s.preco for s in instance.servicos.all()), Decimal('0'))
        rate = Decimal(str(instance.profissional.taxa_comissao))
        if not Decimal('0') <= rate <= Decimal('100') or total < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError('Valor ou comissão inválida.')
        instance.valor_total = total
        instance.valor_comissao = (total * rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        instance.lucro_liquido = total - instance.valor_comissao


@receiver(post_save, sender=Agendamento)
def atualizar_fidelidade(sender, instance, **kwargs):
    from django.db import transaction
    from apps.agenda.models import CartaoFidelidade
    if instance.status != 'CONCLUIDO' or getattr(instance, '_previous_status', None) == 'CONCLUIDO':
        return
    if not instance.empresa.fidelidade_ativo:
        return
    with transaction.atomic():
        cartao, _ = CartaoFidelidade.objects.get_or_create(empresa=instance.empresa, cliente=instance.cliente)
        cartao = CartaoFidelidade.objects.select_for_update().get(pk=cartao.pk)
        cartao.qtd_selos_atual += 1
        if cartao.qtd_selos_atual >= instance.empresa.fidelidade_meta:
            cartao.premios_disponiveis += 1
            cartao.qtd_selos_atual = 0
        cartao.save()


def _notificar_cancelamento(instance) -> None:
    """
    Verifica se um agendamento foi cancelado. Se sim, procura na Fila de Espera 
    por alguém que queria esse horário e simula a notificação.
    """
    if instance.status == 'CANCELADO':
        from zoneinfo import ZoneInfo
        fuso_local = ZoneInfo('America/Sao_Paulo')
        datetime_local = instance.data_hora_inicio.astimezone(fuso_local)
        data_formatada = datetime_local.strftime('%d/%m/%Y às %H:%M')
        
        data = datetime_local.date()
        horario = datetime_local.time().replace(tzinfo=None)
        
        session_id = f"tenant_{instance.empresa.id}" if instance.empresa else 'default'
        cliente_nome = instance.cliente.get_full_name() or instance.cliente.username if instance.cliente else "Desconhecido"
        
        from services.waha_service import enviar_mensagem_whatsapp
        
        # Avisa o barbeiro sobre o cancelamento
        if instance.profissional and instance.profissional.telefone:
            msg_barbeiro = (
                f"❌ *Agendamento Cancelado*\n\n"
                f"O cliente *{cliente_nome}* cancelou o horário de {data_formatada}.\n"
                f"O horário está livre agora."
            )
            try:
                enviar_mensagem_whatsapp(instance.profissional.telefone, msg_barbeiro, waha_session=session_id)
            except Exception as e:
                logger.error(f"Erro ao notificar barbeiro do cancelamento: {e}")
                
        nome_salao = instance.empresa.nome if instance.empresa else "Salão Pro"
        
        # Avisa o cliente sobre o cancelamento
        if instance.cliente and instance.cliente.telefone:
            msg_cliente = (
                f"Olá, {cliente_nome}!\n\n"
                f"Seu agendamento para o dia {data_formatada} foi *cancelado* com sucesso.\n"
                f"Esperamos ver você em breve no {nome_salao}!"
            )
            try:
                enviar_mensagem_whatsapp(instance.cliente.telefone, msg_cliente, waha_session=session_id)
            except Exception as e:
                logger.error(f"Erro ao notificar cliente do cancelamento: {e}")
            
        espera = FilaEspera.objects.filter(
            empresa=instance.empresa,
            data_desejada=data,
            horario_desejado=horario,
            notificado=False
        ).order_by('criado_em').first()
        
        if espera:
            espera.notificado = True
            espera.save()
            logger.info(f"Notificando {espera.cliente_nome} ({espera.cliente_telefone}) sobre vaga liberada em {data} às {horario}.")
            
            # Notifica o cliente da fila de espera
            from services.waha_service import enviar_mensagem_whatsapp
            msg_fila = (
                f"Olá, {espera.cliente_nome}!\n\n"
                f"Uma vaga acabou de ser liberada na barbearia para o dia {data.strftime('%d/%m/%Y')} às {horario.strftime('%H:%M')}!\n"
                f"Acesse o app para agendar antes que outra pessoa pegue."
            )
            enviar_mensagem_whatsapp(espera.cliente_telefone, msg_fila, waha_session=session_id)

@receiver(post_save, sender=Agendamento)
def sniper_de_desistencias(sender, instance, created, **kwargs):
    from django.db import transaction
    if instance.status != 'CANCELADO' or getattr(instance, '_previous_status', None) == 'CANCELADO':
        return
    def notify():
        try:
            _notificar_cancelamento(Agendamento.objects.get(pk=instance.pk))
        except Exception:
            logger.exception('Falha na notificação do cancelamento %s', instance.pk)
    transaction.on_commit(notify)
