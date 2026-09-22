from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_manager(user):
    return bool(user.is_authenticated and (
        user.is_superuser or (user.tipo == 'ADMINISTRADOR' and user.empresa_id and user.empresa.ativo)
    ))


class PublicReadAdminWrite(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_manager(request.user)


class IsTenantAdmin(BasePermission):
    message = 'Apenas administradores podem acessar esta funcionalidade.'

    def has_permission(self, request, view):
        return is_manager(request.user)


class CompanyPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        if view.action in ('create', 'destroy'):
            return request.user.is_superuser
        return is_manager(request.user)

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

# Compatibility for existing tenant/WAHA view imports.
IsAdminUserOrReadOnly = PublicReadAdminWrite
