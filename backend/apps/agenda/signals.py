import logging
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from apps.agenda.models import Agendamento

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Agendamento)
def schedule_confirmation(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: enviar_confirmacao_agendamento(instance.pk))


def enviar_confirmacao_agendamento(appointment_id):
    # Executa depois do commit, com serviços já vinculados. Falha de SMTP não desfaz a reserva.
    try:
        instance = Agendamento.objects.select_related('cliente', 'profissional', 'empresa').get(pk=appointment_id)
        if not instance.cliente.email:
            return
        services = ', '.join(s.nome for s in instance.servicos.all())
        date = timezone.localtime(instance.data_hora_inicio).strftime('%d/%m/%Y às %H:%M')
        send_mail(
            subject=f"Agendamento registrado - {instance.empresa.nome}",
            message=(
                f"Olá, {instance.cliente.get_full_name() or instance.cliente.username}!\n\n"
                f"Seu agendamento foi registrado e aguarda confirmação.\n"
                f"Profissional: {instance.profissional.get_full_name() or instance.profissional.username}\n"
                f"Serviços: {services}\nData: {date}\n\n"
                "Acompanhe o status na sua agenda."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.cliente.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception('Falha na notificação do agendamento %s', appointment_id)
