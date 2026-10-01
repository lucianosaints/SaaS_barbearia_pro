from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.tenants.models import Empresa

class Command(BaseCommand):
    help = 'Verifica e expira os trials de empresas cuja data_fim_trial já passou.'

    def handle(self, *args, **options):
        hoje = timezone.now().date()
        # Busca empresas que estão em trial e cuja data de fim já passou
        empresas_expiradas = Empresa.objects.filter(
            em_trial=True,
            data_fim_trial__lt=hoje
        )
        
        count = 0
        for empresa in empresas_expiradas:
            empresa.em_trial = False
            empresa.save(update_fields=['em_trial'])
            count += 1
            self.stdout.write(self.style.WARNING(f'Trial expirado para: {empresa.nome} (ID: {empresa.id})'))
            
        self.stdout.write(self.style.SUCCESS(f'Rotina finalizada. {count} empresas tiveram o trial expirado.'))
