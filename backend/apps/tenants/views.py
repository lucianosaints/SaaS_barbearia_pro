from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.tenants.models import Empresa
from apps.tenants.serializers import EmpresaSerializer

class EmpresaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para visualização e edição de dados da Empresa.
    Aplica o isolamento de tenant para garantir que cada usuário
    acesse apenas os dados da própria empresa.
    """
    serializer_class = EmpresaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Se for superusuário, pode ver todas as empresas
        if user.is_superuser:
            return Empresa.objects.all()
        # Caso contrário, apenas a empresa vinculada ao usuário
        if user.empresa:
            return Empresa.objects.filter(id=user.empresa.id)
        return Empresa.objects.none()
