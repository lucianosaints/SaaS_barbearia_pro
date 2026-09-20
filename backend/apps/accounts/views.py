from django.db import IntegrityError, transaction
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, SAFE_METHODS
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.accounts.models import Usuario
from apps.accounts.permissions import PublicReadAdminWrite, is_manager
from apps.accounts.serializers import (
    UsuarioSerializer, ProfissionalPublicoSerializer, RegistroClienteSerializer,
    CustomTokenObtainPairSerializer,
)


class AuthThrottle(AnonRateThrottle):
    scope = 'auth'

    def get_cache_key(self, request, view):
        # O cadastro continua limitado mesmo quando quem o chama já tem uma sessão.
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [AuthThrottle]


class CustomTokenRefreshView(TokenRefreshView):
    throttle_classes = [AuthThrottle]


class UsuarioViewSet(viewsets.ModelViewSet):
    permission_classes = [PublicReadAdminWrite]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_serializer_class(self):
        return UsuarioSerializer if is_manager(self.request.user) else ProfissionalPublicoSerializer

    def get_queryset(self):
        user = self.request.user
        empresa_id = self.request.query_params.get('empresa_id')
        if empresa_id and self.request.method in SAFE_METHODS:
            if not empresa_id.isdigit():
                raise ValidationError({'empresa_id': 'Identificador inválido.'})
            # Consulta pública nunca devolve campos privados mesmo para gestores de outra empresa.
            return Usuario.objects.filter(empresa_id=empresa_id, tipo='PROFISSIONAL', is_active=True, empresa__ativo=True)
        if is_manager(user):
            if user.is_superuser:
                return Usuario.objects.all()
            return Usuario.objects.filter(empresa=user.empresa, is_superuser=False, is_staff=False)
        if user.is_authenticated and user.tipo == 'PROFISSIONAL' and user.empresa_id:
            return Usuario.objects.filter(empresa=user.empresa, tipo='PROFISSIONAL', is_active=True)
        return Usuario.objects.filter(tipo='PROFISSIONAL', is_active=True, empresa__ativo=True)

    def get_serializer(self, *args, **kwargs):
        if self.request.query_params.get('empresa_id') and self.request.method in SAFE_METHODS:
            kwargs.setdefault('context', self.get_serializer_context())
            return ProfissionalPublicoSerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthThrottle])
def registrar_cliente(request):
    serializer = RegistroClienteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    names = data['nome'].split(' ', 1)
    try:
        with transaction.atomic():
            usuario = Usuario.objects.create_user(
                username=data['email'], email=data['email'], password=data['senha'],
                first_name=names[0], last_name=names[1] if len(names) > 1 else '',
                telefone=data.get('telefone', ''), tipo='CLIENTE', empresa_id=data.get('empresa_id'),
            )
    except IntegrityError:
        raise ValidationError({'email': 'Já existe um usuário com este e-mail.'})
    refresh = RefreshToken.for_user(usuario)
    return Response({
        'refresh': str(refresh), 'access': str(refresh.access_token),
        'user': {'id': usuario.id, 'nome': usuario.get_full_name(), 'email': usuario.email, 'tipo': usuario.tipo},
    }, status=status.HTTP_201_CREATED)
