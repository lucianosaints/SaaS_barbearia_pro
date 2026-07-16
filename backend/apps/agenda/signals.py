from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from apps.agenda.models import Agendamento, FilaEspera
import logging

logger = logging.getLogger(__name__)

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
                    assunto = f"Confirmação de Agendamento - Salão Pro"
                    corpo_mensagem = (
                        f"Olá, {cliente_nome}!\n\n"
                        f"Seu agendamento no Salão Pro foi registrado com sucesso!\n\n"
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

            # NOTIFICAÇÃO DO BARBEIRO VIA WAHA
            try:
                if inst.profissional and getattr(inst.profissional, 'telefone', None):
                    from services.waha_service import enviar_mensagem_whatsapp
                    
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
                    
                    msg_barbeiro = (
                        f"💈 *Novo Agendamento no Salão Pro!*\n\n"
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

                    session_id = f"tenant_{inst.empresa.id}" if inst.empresa else 'default'
                    enviar_mensagem_whatsapp(inst.profissional.telefone, msg_barbeiro, waha_session=session_id)
            except Exception as e:
                logger.error(f"Falha ao enviar WAHA para agendamento {inst.id}: {str(e)}")

            # NOTIFICAÇÃO DO CLIENTE VIA WAHA
            try:
                if inst.cliente and getattr(inst.cliente, 'telefone', None):
                    from services.waha_service import enviar_mensagem_whatsapp
                    
                    msg_cliente = (
                        f"Olá, {cliente_nome}!\n\n"
                        f"Seu agendamento no *Salão Pro* foi registrado!\n\n"
                        f"💈 *Detalhes do seu horário:*\n"
                        f"👤 Profissional: {barbeiro_nome}\n"
                        f"📅 Data/Hora: {data_formatada}\n"
                        f"✂️ Serviço(s): {lista_servicos}\n"
                    )

                    empresa = inst.empresa
                    cliente_exige_sinal = (inst.cliente and getattr(inst.cliente, 'status', 'ATIVO') == 'EXIGIR_SINAL')
                    empresa_exige_sinal = getattr(empresa, 'exigir_sinal', False)
                    
                    if empresa and (empresa_exige_sinal or cliente_exige_sinal) and getattr(empresa, 'chave_pix', ''):
                        total_servicos = sum(s.preco for s in inst.servicos.all())
                        valor_sinal = total_servicos / 2
                        chave = empresa.chave_pix
                        beneficiario = getattr(empresa, 'beneficiario_pix', '')
                        
                        msg_cliente += (
                            f"\n⚠️ *ATENÇÃO: CONFIRMAÇÃO NECESSÁRIA*\n"
                            f"Para garantir sua vaga, exigimos o pagamento de um sinal de 50% do valor do serviço.\n\n"
                            f"💰 *Valor do Sinal:* R$ {valor_sinal:.2f}\n"
                            f"🔑 *Chave PIX:* `{chave}`\n"
                        )
                        if beneficiario:
                            msg_cliente += f"👤 *Beneficiário:* {beneficiario}\n"
                        
                        msg_cliente += (
                            f"\nEnvie o comprovante de pagamento em até *15 minutos* para que sua vaga não seja cancelada.\n"
                        )
                    else:
                        msg_cliente += f"\nCaso precise remarcar ou cancelar, acesse nosso app.\n"
                        msg_cliente += f"Agradecemos a preferência!"

                    session_id = f"tenant_{inst.empresa.id}" if inst.empresa else 'default'
                    enviar_mensagem_whatsapp(inst.cliente.telefone, msg_cliente, waha_session=session_id)
            except Exception as e:
                logger.error(f"Falha ao enviar WAHA para cliente no agendamento {inst.id}: {str(e)}")

        from django.db import transaction
        transaction.on_commit(disparar_notificacoes)


@receiver(pre_save, sender=Agendamento)
def calcular_valores_financeiros(sender, instance: Agendamento, **kwargs) -> None:
    """
    Signal pre_save para calcular comissão e lucro líquido quando o status
    muda para 'CONCLUIDO'. O valor_total já é preenchido pelo signal m2m_changed
    em models.py no momento da associação dos serviços.
    """
    # Verifica se a instância já existe no banco (para podermos comparar o status antigo)
    status_anterior = None
    if instance.pk:
        try:
            old_instance = Agendamento.objects.get(pk=instance.pk)
            status_anterior = old_instance.status
        except Agendamento.DoesNotExist:
            pass

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

        # Atualiza o Cartão Fidelidade se o status acabou de mudar para CONCLUIDO
        if status_anterior != 'CONCLUIDO' and instance.cliente and instance.empresa:
            if instance.empresa.fidelidade_ativo:
                from apps.agenda.models import CartaoFidelidade
                cartao, _ = CartaoFidelidade.objects.get_or_create(
                    empresa=instance.empresa,
                    cliente=instance.cliente
                )
                cartao.qtd_selos_atual += 1
                
                # Se bateu a meta, zera e dá o prêmio
                if cartao.qtd_selos_atual >= instance.empresa.fidelidade_meta:
                    cartao.premios_disponiveis += 1
                    cartao.qtd_selos_atual = 0
                    
                cartao.save()


@receiver(post_save, sender=Agendamento)
def sniper_de_desistencias(sender, instance: Agendamento, created: bool, **kwargs) -> None:
    """
    Verifica se um agendamento foi cancelado. Se sim, procura na Fila de Espera 
    por alguém que queria esse horário e simula a notificação.
    """
    if instance.status == 'CANCELADO':
        from zoneinfo import ZoneInfo
        fuso_local = ZoneInfo('America/Sao_Paulo')
        datetime_local = instance.data_hora_inicio.astimezone(fuso_local)
        data_formatada = datetime_local.strftime('%d/%m/%Y às %H:%M')
        
        data = instance.data_hora_inicio.date()
        horario = instance.data_hora_inicio.time()
        
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
                
        # Avisa o cliente sobre o cancelamento
        if instance.cliente and instance.cliente.telefone:
            msg_cliente = (
                f"Olá, {cliente_nome}!\n\n"
                f"Seu agendamento para o dia {data_formatada} foi *cancelado* com sucesso.\n"
                f"Esperamos ver você em breve no Salão Pro!"
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
