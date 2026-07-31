from rest_framework import permissions

class IsDemoUserReadOnly(permissions.BasePermission):
    """
    Impede que a conta de demonstração (demo@salaopro.site)
    faça alterações destrutivas em dados sensíveis (perfil, senhas, tenant).
    """
    message = "Ação bloqueada. A conta de demonstração não tem permissão para alterar configurações de perfil, senha ou dados da barbearia."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user and request.user.is_authenticated:
            if request.user.email == 'demo@salaopro.site':
                return False
        return True

class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Permissão que permite métodos seguros (GET, HEAD, OPTIONS) para qualquer um,
    mas exige que o usuário seja 'ADMINISTRADOR' ou superuser para criar, editar ou deletar.
    """

    def has_permission(self, request, view):
        # Permite acesso de leitura para qualquer requisição
        if request.method in permissions.SAFE_METHODS:
            return True

        # Permite escrita se o usuário estiver autenticado e for administrador/superuser
        if request.user and request.user.is_authenticated:
            return request.user.is_superuser or request.user.tipo == 'ADMINISTRADOR'
        
        return False
