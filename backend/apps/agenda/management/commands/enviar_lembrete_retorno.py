from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.agenda.models import Agendamento
from services.waha_service import enviar_mensagem_whatsapp

class Command(BaseCommand):
    help = 'Envia lembrete de retorno via WhatsApp para clientes que cortaram há 25 dias e não têm novos agendamentos.'

    def handle(self, *args, **options):
        # 1. Calcular a data alvo: 25 dias atrás
        hoje = timezone.localtime(timezone.now()).date()
        data_alvo = hoje - timedelta(days=25)
        
        self.stdout.write(f"Iniciando verificação de lembretes para a data: {data_alvo}")
        
        # 2. Buscar agendamentos concluídos nesta data
        agendamentos_alvo = Agendamento.objects.filter(
            data_hora_inicio__date=data_alvo,
            status='CONCLUIDO'
        ).select_related('cliente', 'empresa')
        
        clientes_notificados = set()
        
        for agendamento in agendamentos_alvo:
            cliente = agendamento.cliente
            if not cliente or not getattr(cliente, 'telefone', None):
                continue
                
            # Evita mandar duas vezes para o mesmo cliente na mesma execução
            if cliente.id in clientes_notificados:
                continue
                
            # 3. Verificar se o cliente tem algum agendamento futuro
            # Pode ser CONFIRMADO ou PENDENTE
            tem_agendamento_futuro = Agendamento.objects.filter(
                cliente=cliente,
                data_hora_inicio__date__gte=hoje,
                status__in=['CONFIRMADO', 'PENDENTE']
            ).exists()
            
            if not tem_agendamento_futuro:
                cliente_nome = cliente.get_full_name() or cliente.username
                
                # Opcionalmente, pode ser interessante enviar o link com o slug da empresa
                # url_agendamento = f"https://barbeiropro.duckdns.org/agendar/{agendamento.empresa.slug}" if agendamento.empresa else "https://barbeiropro.duckdns.org"
                url_agendamento = "https://barbeiropro.duckdns.org"
                
                # 4. Enviar mensagem
                msg = (
                    f"Fala, {cliente_nome}! Já faz 25 dias desde o seu último corte no Salão Pro. 💈 "
                    f"Que tal agendar um horário para manter o visual alinhado? "
                    f"Clique aqui para agendar: {url_agendamento}"
                )
                
                session_id = f"tenant_{agendamento.empresa.id}" if agendamento.empresa else 'default'
                
                try:
                    enviar_mensagem_whatsapp(cliente.telefone, msg, waha_session=session_id)
                    clientes_notificados.add(cliente.id)
                    self.stdout.write(self.style.SUCCESS(f"Lembrete enviado para {cliente_nome} ({cliente.telefone})"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Erro ao enviar lembrete para {cliente_nome}: {str(e)}"))
                    
        self.stdout.write(self.style.SUCCESS(f"Processo concluído. {len(clientes_notificados)} lembrete(s) enviado(s)."))
