from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_manager(user):
    return bool(user.is_authenticated and (
        user.is_superuser or (user.tipo == 'ADMINISTRADOR' and user.empresa_id and user.empresa.ativo)
    ))


class PublicReadAdminWrite(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_manager(request.user)


class CompanyPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        if view.action in ('create', 'destroy'):
            return request.user.is_superuser
        return is_manager(request.user)
