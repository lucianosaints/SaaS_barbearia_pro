from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.tenants.models import Empresa, SiteVisitCounter
from apps.tenants.serializers import EmpresaSerializer, EmpresaPublicaSerializer
from apps.accounts.permissions import CompanyPermission, IsDemoUserReadOnly


class SiteVisitThrottle(SimpleRateThrottle):
    scope = 'site_visit'

    def get_rate(self):
        return settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'][self.scope]

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class SiteVisitCounterView(APIView):
    permission_classes = [AllowAny]

    def get_throttles(self):
        return [SiteVisitThrottle()] if self.request.method == 'POST' else []

    def get(self, request):
        counter, _ = SiteVisitCounter.objects.get_or_create(pk=1, defaults={'total': 0})
        return Response({'total': counter.total})

    @transaction.atomic
    def post(self, request):
        SiteVisitCounter.objects.get_or_create(pk=1, defaults={'total': 0})
        SiteVisitCounter.objects.filter(pk=1).update(total=F('total') + 1)
        total = SiteVisitCounter.objects.values_list('total', flat=True).get(pk=1)
        return Response({'total': total}, status=status.HTTP_200_OK)

class EmpresaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para visualização e edição de dados da Empresa.
    Aplica o isolamento de tenant para garantir que cada usuário
    acesse apenas os dados da própria empresa.
    """
    serializer_class = EmpresaSerializer
    permission_classes = [CompanyPermission, IsDemoUserReadOnly]

    def get_serializer_class(self):
        if self.action in ('list', 'por_slug'):
            return EmpresaPublicaSerializer
        return EmpresaSerializer

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
        import logging
        logger = logging.getLogger(__name__)
        
        # Busca direta pela Empresa para busca case-insensitive e validação independente
        empresa = Empresa.objects.filter(slug__iexact=slug).first()
        
        if not empresa or not empresa.ativo:
            logger.warning(f"[Agendamento Público] Barbearia não encontrada ou inativa (ativo=False) para o slug: '{slug}'")
            return Response({"detail": "Barbearia não encontrada ou inativa."}, status=404)
            
        serializer = self.get_serializer(empresa)
        return Response(serializer.data)
