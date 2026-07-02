import os
import django

# Inicializa as configurações do Django no script
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.tenants.models import Empresa
from apps.agenda.models import Servico
from apps.accounts.models import Usuario

def seed():
    print("Semeando banco de dados...")
    
    # 1. Cria a Empresa
    empresa, created = Empresa.objects.get_or_create(
        slug="golden-barber",
        defaults={
            "nome": "Golden Barber Premium",
            "cnpj": "12345678000199",
            "hora_abertura": "09:00:00",
            "hora_fechamento": "19:00:00",
            "intervalo_almoco_inicio": "12:00:00",
            "intervalo_almoco_fim": "13:00:00",
            "ativo": True
        }
    )
    if created:
        print(f"Empresa criada: {empresa.nome}")
    else:
        print(f"Empresa já existente: {empresa.nome}")

    # 2. Cria os Serviços
    servicos_dados = [
        {"nome": "Corte de Cabelo", "preco": 50.00, "duracao_minutos": 30},
        {"nome": "Barba Completa", "preco": 35.00, "duracao_minutos": 30},
        {"nome": "Corte + Barba Premium", "preco": 75.00, "duracao_minutos": 60},
    ]

    for dados in servicos_dados:
        servico, created = Servico.objects.get_or_create(
            empresa=empresa,
            nome=dados["nome"],
            defaults={
                "preco": dados["preco"],
                "duracao_minutos": dados["duracao_minutos"],
                "ativo": True
            }
        )
        if created:
            print(f"Serviço criado: {servico.nome}")

    # 3. Cria um Barbeiro (Profissional)
    barbeiro, created = Usuario.objects.get_or_create(
        username="carlos.barber",
        defaults={
            "email": "carlos.barber@goldenbarber.com",
            "first_name": "Carlos",
            "last_name": "Silva",
            "tipo": "PROFISSIONAL",
            "empresa": empresa,
            "is_active": True
        }
    )
    if created:
        barbeiro.set_password("carlos123")
        barbeiro.save()
        print(f"Barbeiro criado: {barbeiro.first_name} (Username: carlos.barber, Senha: carlos123)")

    print("Banco de dados semeado com sucesso! 🎉")

if __name__ == "__main__":
    seed()
