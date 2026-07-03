from rest_framework import permissions

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
