from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsEmpresaAtiva(BasePermission):
    """
    Permite métodos seguros (GET, HEAD, OPTIONS) para todos,
    mas exige que a empresa tenha assinatura ativa ou esteja no período de teste
    para realizar operações de escrita (POST, PUT, PATCH, DELETE).
    """

    def has_permission(self, request, view):
        # Permite requisições de leitura sempre
        if request.method in SAFE_METHODS:
            return True

        # Para ações que modifiquem dados, exige autenticação e empresa
        if not request.user or not request.user.is_authenticated:
            return False

        # Clientes finais não tem validação de empresa (as regras deles já existem nas próprias views)
        if request.user.tipo == 'CLIENTE':
            return True

        # Se for superusuário, permite tudo
        if request.user.is_superuser:
            return True

        empresa = request.user.empresa
        if not empresa:
            return False

        # Verifica a "Fechadura": Se a assinatura está ativa ou ainda no período de trial
        if empresa.assinatura_ativa or empresa.em_trial:
            return True

        return False
