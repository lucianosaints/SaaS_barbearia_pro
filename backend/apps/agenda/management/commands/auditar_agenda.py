from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from apps.agenda.models import Agendamento, Servico
from apps.accounts.models import Usuario
from apps.tenants.models import Empresa


class Command(BaseCommand):
    help = 'Auditoria somente leitura dos dados legados antes da atualização.'

    def add_arguments(self, parser):
        parser.add_argument('--fail-on-issues', action='store_true')

    def handle(self, *args, **options):
        issues = []
        for company in Empresa.objects.iterator():
            start, end = company.intervalo_almoco_inicio, company.intervalo_almoco_fim
            if company.hora_abertura >= company.hora_fechamento or (start is None) != (end is None) or (start is not None and end is not None and not company.hora_abertura <= start < end <= company.hora_fechamento):
                issues.append(f'Empresa {company.pk}: expediente inválido.')
        for service in Servico.objects.iterator():
            if service.preco < 0 or service.duracao_minutos <= 0:
                issues.append(f'Serviço {service.pk}: preço/duração inválidos.')
        for user in Usuario.objects.filter(tipo='PROFISSIONAL').iterator():
            if not user.empresa_id or not Decimal('0') <= user.taxa_comissao <= Decimal('100'):
                issues.append(f'Profissional {user.pk}: empresa/comissão inválida.')
        appointments = Agendamento.objects.select_related('profissional', 'cliente').prefetch_related('servicos').order_by('profissional_id', 'data_hora_inicio')
        latest = {}
        for appointment in appointments.iterator(chunk_size=500):
            services = list(appointment.servicos.all())
            company_mismatch = (
                appointment.profissional.empresa_id != appointment.empresa_id
                or any(service.empresa_id != appointment.empresa_id for service in services)
            )
            profile_mismatch = (
                appointment.profissional.tipo != 'PROFISSIONAL'
                or appointment.cliente.tipo != 'CLIENTE'
            )
            if company_mismatch or (profile_mismatch and appointment.status not in ('CONCLUIDO', 'CANCELADO')):
                issues.append(f'Agendamento {appointment.pk}: perfil ou empresa incompatível.')
            if not services or not appointment.data_hora_fim or appointment.data_hora_fim <= appointment.data_hora_inicio:
                issues.append(f'Agendamento {appointment.pk}: serviços/término inválidos.')
            if appointment.status == 'CONCLUIDO':
                values = (appointment.valor_total, appointment.valor_comissao, appointment.lucro_liquido)
                if any(v is None or v < 0 for v in values) or (all(v is not None for v in values) and values[0] != values[1] + values[2]):
                    issues.append(f'Agendamento {appointment.pk}: valores financeiros incompletos/inconsistentes.')
            if appointment.status != 'CANCELADO' and appointment.data_hora_fim:
                previous = latest.get(appointment.profissional_id)
                if previous and previous.data_hora_fim > appointment.data_hora_inicio:
                    issues.append(f'Agendamentos {previous.pk}/{appointment.pk}: sobreposição.')
                if previous is None or appointment.data_hora_fim > previous.data_hora_fim:
                    latest[appointment.profissional_id] = appointment
        for issue in issues:
            self.stdout.write(issue)
        self.stdout.write(f'{len(issues)} inconsistência(s). Nenhum dado foi alterado.')
        if issues and options['fail_on_issues']:
            raise CommandError('Revise os registros indicados antes de liberar a atualização.')
