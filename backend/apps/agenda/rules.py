"""Regras compartilhadas pela disponibilidade e gravação de reservas."""
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from .models import Agendamento

ACTIVE_STATUSES = ('PENDENTE', 'CONFIRMADO', 'CONCLUIDO')


def validate_selection(profissional, servicos):
    if not profissional or profissional.tipo != 'PROFISSIONAL' or not profissional.is_active:
        raise ValidationError({'profissional': 'Selecione um profissional ativo.'})
    if not profissional.empresa_id or not profissional.empresa.ativo:
        raise ValidationError({'profissional': 'A barbearia não está ativa.'})
    if not servicos or len({s.pk for s in servicos}) != len(servicos):
        raise ValidationError({'servicos': 'Selecione ao menos um serviço, sem repetições.'})
    if any(not s.ativo or s.empresa_id != profissional.empresa_id or s.duracao_minutos <= 0 or s.preco < 0 for s in servicos):
        raise ValidationError({'servicos': 'Os serviços devem estar ativos e pertencer à barbearia do profissional.'})
    return sum(s.duracao_minutos for s in servicos)


def validate_slot(profissional, servicos, inicio, exclude_id=None):
    duration = validate_selection(profissional, servicos)
    inicio = timezone.localtime(inicio)
    fim = inicio + timedelta(minutes=duration)
    empresa = profissional.empresa
    if inicio <= timezone.now():
        raise ValidationError({'data_hora_inicio': 'Escolha um horário futuro.'})
    if inicio.date() != fim.date() or inicio.time() < empresa.hora_abertura or fim.time() > empresa.hora_fechamento:
        raise ValidationError({'data_hora_inicio': 'O atendimento deve caber no expediente.'})
    if empresa.intervalo_almoco_inicio and empresa.intervalo_almoco_fim:
        if inicio.time() < empresa.intervalo_almoco_fim and fim.time() > empresa.intervalo_almoco_inicio:
            raise ValidationError({'data_hora_inicio': 'O atendimento coincide com o intervalo de almoço.'})
    conflicts = Agendamento.objects.filter(
        profissional=profissional, status__in=ACTIVE_STATUSES,
        data_hora_inicio__lt=fim,
    ).exclude(pk=exclude_id)
    # Reservas antigas sem término não devem liberar horários silenciosamente.
    if conflicts.filter(Q(data_hora_fim__gt=inicio) | Q(data_hora_fim__isnull=True)).exists():
        raise ValidationError({'data_hora_inicio': 'Este horário não está mais disponível. Escolha outro.'})
    return fim


def available_slots(profissional, servicos, day):
    duration = validate_selection(profissional, servicos)
    if day < timezone.localdate():
        return []
    empresa = profissional.empresa
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(day, empresa.hora_abertura), tz)
    end = timezone.make_aware(datetime.combine(day, empresa.hora_fechamento), tz)
    result = []
    while start + timedelta(minutes=duration) <= end:
        try:
            validate_slot(profissional, servicos, start)
        except ValidationError:
            pass
        else:
            result.append(start.strftime('%H:%M'))
        start += timedelta(minutes=30)
    return result
