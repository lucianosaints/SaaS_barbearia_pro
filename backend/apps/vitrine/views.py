from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import PublicReadAdminWrite
from .models import Produto
from .serializers import ProdutoSerializer


class ProdutoViewSet(ModelViewSet):
    serializer_class = ProdutoSerializer
    permission_classes = [PublicReadAdminWrite]
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        empresa_id = self.request.query_params.get('empresa_id')
        empresa_slug = self.request.query_params.get('empresa_slug')

        if user.is_authenticated and user.is_superuser and not (empresa_id or empresa_slug):
            return Produto.objects.select_related('empresa').all()
        if user.is_authenticated and getattr(user, 'empresa_id', None) and not (empresa_id or empresa_slug):
            return Produto.objects.filter(empresa=user.empresa)

        if not empresa_id and not empresa_slug:
            raise ValidationError({'empresa': 'Informe o salão para consultar a vitrine.'})
        if empresa_id and not empresa_id.isdigit():
            raise ValidationError({'empresa_id': 'Identificador inválido.'})

        filtros = {'empresa__ativo': True, 'disponivel': True}
        if empresa_id:
            filtros['empresa_id'] = empresa_id
        else:
            filtros['empresa__slug__iexact'] = empresa_slug
        return Produto.objects.filter(**filtros)

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            serializer.save(empresa=self.request.user.empresa)
        else:
            serializer.save()

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]
