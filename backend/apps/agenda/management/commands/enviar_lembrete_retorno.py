from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.agenda.models import Agendamento
from services.waha_service import enviar_mensagem_whatsapp

class Command(BaseCommand):
    help = 'Envia lembrete de retorno via WhatsApp para clientes que cortaram há 25 dias e não têm novos agendamentos.'

    def handle(self, *args, **options):
        from apps.tenants.models import Empresa
        
        hoje = timezone.localtime(timezone.now()).date()
        clientes_notificados = set()
        empresas = Empresa.objects.filter(ativo=True)
        
        self.stdout.write(f"Iniciando verificação de lembretes hoje: {hoje}")
        
        for empresa in empresas:
            dias_retorno = empresa.dias_retorno_lembrete
            if not dias_retorno or dias_retorno <= 0:
                continue
                
            data_alvo = hoje - timedelta(days=dias_retorno)
            
            # Buscar agendamentos concluídos nesta data para esta empresa
            agendamentos_alvo = Agendamento.objects.filter(
                empresa=empresa,
                data_hora_inicio__date=data_alvo,
                status='CONCLUIDO'
            ).select_related('cliente')
            
            for agendamento in agendamentos_alvo:
                cliente = agendamento.cliente
                if not cliente or not getattr(cliente, 'telefone', None):
                    continue
                    
                # Evita mandar duas vezes para o mesmo cliente na mesma execução
                if cliente.id in clientes_notificados:
                    continue
                    
                # Verificar se o cliente tem algum agendamento futuro
                tem_agendamento_futuro = Agendamento.objects.filter(
                    cliente=cliente,
                    data_hora_inicio__date__gte=hoje,
                    status__in=['CONFIRMADO', 'PENDENTE']
                ).exists()
                
                if not tem_agendamento_futuro:
                    cliente_nome = cliente.get_full_name() or cliente.username
                    url_agendamento = "https://barbeiropro.duckdns.org"
                    
                    msg = (
                        f"Fala, {cliente_nome}! Já faz {dias_retorno} dias desde o seu último corte no Salão Pro. 💈 "
                        f"Que tal agendar um horário para manter o visual alinhado? "
                        f"Clique aqui para agendar: {url_agendamento}"
                    )
                    
                    session_id = f"tenant_{empresa.id}"
                    
                    try:
                        enviar_mensagem_whatsapp(cliente.telefone, msg, waha_session=session_id)
                        clientes_notificados.add(cliente.id)
                        self.stdout.write(self.style.SUCCESS(f"[{empresa.nome}] Lembrete de {dias_retorno} dias enviado para {cliente_nome} ({cliente.telefone})"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"[{empresa.nome}] Erro ao enviar lembrete para {cliente_nome}: {str(e)}"))
                        
        self.stdout.write(self.style.SUCCESS(f"Processo concluído. {len(clientes_notificados)} lembrete(s) enviado(s)."))
