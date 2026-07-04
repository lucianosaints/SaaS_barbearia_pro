from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.tenants.models import Empresa
from apps.tenants.serializers import EmpresaSerializer
from apps.accounts.permissions import IsAdminUserOrReadOnly

class EmpresaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para visualização e edição de dados da Empresa.
    Aplica o isolamento de tenant para garantir que cada usuário
    acesse apenas os dados da própria empresa.
    """
    serializer_class = EmpresaSerializer
    permission_classes = [IsAdminUserOrReadOnly]

    def get_queryset(self):
        # Permitir que qualquer pessoa veja as empresas ativas E (com assinatura ativa OU em trial)
        if self.action == 'list' or self.action == 'por_slug':
            return Empresa.objects.filter(
                Q(ativo=True) & (Q(assinatura_ativa=True) | Q(em_trial=True))
            )

        user = self.request.user
        if user.is_authenticated:
            # Se for superusuário, pode ver todas as empresas
            if user.is_superuser:
                return Empresa.objects.all()
            # Caso contrário, apenas a empresa vinculada ao usuário
            if user.empresa:
                return Empresa.objects.filter(id=user.empresa.id)
                
        return Empresa.objects.none()

    @action(detail=False, methods=['get'], url_path=r'por-slug/(?P<slug>[-\w]+)', permission_classes=[AllowAny])
    def por_slug(self, request, slug=None):
        """Busca uma empresa publicamente pelo slug"""
        empresa = self.get_queryset().filter(slug=slug).first()
        if empresa:
            serializer = self.get_serializer(empresa)
            return Response(serializer.data)
        return Response({"detail": "Barbearia não encontrada ou inativa."}, status=404)
