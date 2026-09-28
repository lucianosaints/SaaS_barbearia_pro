from django.db import IntegrityError, transaction
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db.models import Q
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, SAFE_METHODS, IsAuthenticated
from rest_framework.views import APIView
from apps.tenants.permissions import IsEmpresaAtiva
from apps.accounts.permissions import IsDemoUserReadOnly
from rest_framework.decorators import api_view, permission_classes, throttle_classes, action
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.accounts.models import Usuario
from apps.accounts.permissions import PublicReadAdminWrite, is_manager
from apps.accounts.serializers import (
    UsuarioSerializer, ProfissionalPublicoSerializer, RegistroClienteSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetConfirmSerializer, PasswordResetRequestSerializer,
)


class AuthIPThrottle(AnonRateThrottle):
    scope = 'auth_ip'

    def get_rate(self):
        return settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES', {}).get(self.scope)

    def get_cache_key(self, request, view):
        # O cadastro continua limitado mesmo quando quem o chama já tem uma sessão.
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class AuthAccountThrottle(SimpleRateThrottle):
    scope = 'auth_account'

    def get_rate(self):
        return settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES', {}).get(self.scope)

    def get_cache_key(self, request, view):
        import hashlib
        identity = str(
            request.data.get('username') or request.data.get('email') or
            request.data.get('refresh') or ''
        ).strip().casefold()
        if not identity:
            return None
        digest = hashlib.sha256(identity.encode('utf-8')).hexdigest()
        return self.cache_format % {'scope': self.scope, 'ident': digest}


# Compatibilidade para imports de testes/integrações anteriores.
AuthThrottle = AuthIPThrottle


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [AuthIPThrottle, AuthAccountThrottle]


class CustomTokenRefreshView(TokenRefreshView):
    throttle_classes = [AuthIPThrottle, AuthAccountThrottle]


PASSWORD_RESET_RESPONSE = {
    'detail': 'Se existir uma conta ativa para esse e-mail, enviaremos as instruções de recuperação.'
}


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthIPThrottle, AuthAccountThrottle])
def solicitar_recuperacao_senha(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    usuario = Usuario.objects.filter(
        Q(email__iexact=email) | Q(username__iexact=email),
        is_active=True,
    ).order_by('pk').first()

    if usuario and usuario.email:
        uid = urlsafe_base64_encode(force_bytes(usuario.pk))
        token = default_token_generator.make_token(usuario)
        base_url = settings.PUBLIC_FRONTEND_URL.rstrip('/')
        link = f'{base_url}/redefinir-senha?uid={uid}&token={token}'
        nome = usuario.get_full_name() or usuario.username
        send_mail(
            subject='Recuperação de senha — Salão Pro',
            message=(
                f'Olá, {nome}!\n\n'
                'Recebemos uma solicitação para redefinir sua senha no Salão Pro.\n'
                f'Acesse o link abaixo em até {settings.PASSWORD_RESET_TIMEOUT // 60} minutos:\n\n'
                f'{link}\n\n'
                'Se você não solicitou essa alteração, ignore esta mensagem. Sua senha continuará a mesma.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            fail_silently=True,
        )

    return Response(PASSWORD_RESET_RESPONSE, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthIPThrottle, AuthAccountThrottle])
def confirmar_recuperacao_senha(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        usuario_id = force_str(urlsafe_base64_decode(data['uid']))
        usuario = Usuario.objects.get(pk=usuario_id, is_active=True)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        usuario = None

    if not usuario or not default_token_generator.check_token(usuario, data['token']):
        return Response({'detail': 'Link inválido ou expirado. Solicite uma nova recuperação.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(data['nova_senha'], usuario)
    except DjangoValidationError as exc:
        raise ValidationError({'nova_senha': exc.messages})

    usuario.set_password(data['nova_senha'])
    usuario.save(update_fields=['password'])
    for outstanding in OutstandingToken.objects.filter(user=usuario):
        BlacklistedToken.objects.get_or_create(token=outstanding)
    cache.set(
        f'user_tokens_valid_after:{usuario.pk}',
        int(timezone.now().timestamp()),
        timeout=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()) + 60,
    )
    return Response({'detail': 'Senha redefinida com sucesso. Entre novamente com a nova senha.'})


class UsuarioViewSet(viewsets.ModelViewSet):
    permission_classes = [PublicReadAdminWrite, IsEmpresaAtiva, IsDemoUserReadOnly]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'me':
            return UsuarioSerializer
        return UsuarioSerializer if is_manager(self.request.user) else ProfissionalPublicoSerializer

    def get_queryset(self):
        user = self.request.user
        empresa_id = self.request.query_params.get('empresa_id')
        if not empresa_id and not user.is_authenticated:
            raise ValidationError({'empresa_id': 'Informe a empresa para consultar profissionais.'})
        if empresa_id and self.request.method in SAFE_METHODS:
            if not empresa_id.isdigit():
                raise ValidationError({'empresa_id': 'Identificador inválido.'})
            # Consulta pública nunca devolve campos privados mesmo para gestores de outra empresa.
            return Usuario.objects.filter(empresa_id=empresa_id, tipo__in=['PROFISSIONAL', 'ADMINISTRADOR'], is_staff=False, is_superuser=False, is_active=True, empresa__ativo=True)
        if is_manager(user):
            if user.is_superuser:
                return Usuario.objects.all()
            return Usuario.objects.filter(empresa=user.empresa, is_superuser=False, is_staff=False)
        if user.is_authenticated and user.tipo == 'PROFISSIONAL' and user.empresa_id:
            return Usuario.objects.filter(empresa=user.empresa, tipo__in=['PROFISSIONAL', 'ADMINISTRADOR'], is_staff=False, is_superuser=False, is_active=True)
        return Usuario.objects.filter(tipo__in=['PROFISSIONAL', 'ADMINISTRADOR'], is_staff=False, is_superuser=False, is_active=True, empresa__ativo=True)

    def get_serializer(self, *args, **kwargs):
        if self.action != 'me' and self.request.query_params.get('empresa_id') and self.request.method in SAFE_METHODS:
            kwargs.setdefault('context', self.get_serializer_context())
            return ProfissionalPublicoSerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)

    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated, IsDemoUserReadOnly])
    def me(self, request):
        usuario = request.user
        if not getattr(usuario, 'is_authenticated', False):
            return Response({"error": "Não autenticado"}, status=status.HTTP_401_UNAUTHORIZED)
            
        if request.method == 'GET':
            serializer = self.get_serializer(usuario)
            return Response(serializer.data)
            
        elif request.method == 'PATCH':
            data = request.data.copy()
            # Bloqueia a alteração de campos sensíveis que o usuário NÃO pode alterar sobre si mesmo
            campos_proibidos = [
                'email', 'tipo', 'is_staff', 'is_superuser', 'is_active',
                'empresa', 'status', 'taxa_comissao', 'comissao_percentual'
            ]
            for campo in campos_proibidos:
                data.pop(campo, None)
            
            serializer = self.get_serializer(usuario, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthIPThrottle, AuthAccountThrottle])
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
                aceitou_termos=True, data_aceite_termos=timezone.now(),
                ip_aceite_termos=request.META.get('REMOTE_ADDR'),
            )
    except IntegrityError:
        raise ValidationError({'detail': 'Não foi possível concluir o cadastro. Verifique os dados informados.'})
    refresh = RefreshToken.for_user(usuario)
    return Response({
        'refresh': str(refresh), 'access': str(refresh.access_token),
        'user': {'id': usuario.id, 'nome': usuario.get_full_name(), 'email': usuario.email, 'tipo': usuario.tipo, 'empresa': {'id': usuario.empresa_id, 'slug': usuario.empresa.slug, 'em_trial': usuario.empresa.em_trial, 'assinatura_ativa': usuario.empresa.assinatura_ativa} if usuario.empresa else None},
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthIPThrottle, AuthAccountThrottle])
@transaction.atomic
def registrar_saas(request):
    """
    Cadastra uma nova barbearia (Empresa) e o usuário administrador.
    Inicia o período de teste grátis (Trial).
    """
    from datetime import timedelta
    from django.utils.text import slugify
    from apps.tenants.models import Empresa

    nome_barbearia = request.data.get('nome_barbearia')
    nome_admin = request.data.get('nome_admin')
    email = str(request.data.get('email') or '').strip().lower()
    senha = request.data.get('senha')
    whatsapp = request.data.get('whatsapp')
    aceitou_termos = request.data.get('aceitou_termos') is True

    if not all([nome_barbearia, nome_admin, email, senha, whatsapp]):
        return Response(
            {"error": "Não foi possível concluir o cadastro. Verifique os dados informados."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if Usuario.objects.filter(username=email).exists() or Usuario.objects.filter(email=email).exists():
        return Response(
            {"error": "Não foi possível concluir o cadastro. Verifique os dados informados."},
            status=status.HTTP_400_BAD_REQUEST
        )

    registration = RegistroClienteSerializer(data={'nome': nome_admin, 'email': email, 'senha': senha, 'telefone': whatsapp, 'aceitou_termos': aceitou_termos})
    registration.is_valid(raise_exception=True)

    # Criar a Empresa com 30 dias de trial
    base_slug = slugify(nome_barbearia)
    slug = base_slug
    counter = 1
    while Empresa.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    empresa = Empresa.objects.create(
        nome=nome_barbearia,
        slug=slug,
        em_trial=True,
        data_fim_trial=timezone.now().date() + timedelta(days=30),
        ativo=True
    )

    # Separa primeiro e último nome
    nomes = nome_admin.strip().split(' ', 1)
    first_name = nomes[0]
    last_name = nomes[1] if len(nomes) > 1 else ''

    usuario = Usuario(
        username=email,
        email=email,
        first_name=first_name,
        last_name=last_name,
        telefone=whatsapp,
        tipo='ADMINISTRADOR',
        is_active=True,
        empresa=empresa,
        aceitou_termos=True,
        data_aceite_termos=timezone.now(),
        ip_aceite_termos=request.META.get('REMOTE_ADDR'),
    )
    usuario.set_password(senha)
    usuario.save()

    # Gerar JWT
    refresh = RefreshToken.for_user(usuario)

    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'id': usuario.id,
            'nome': usuario.get_full_name() or usuario.username,
            'email': usuario.email,
            'tipo': usuario.tipo,
            'empresa': {
                'id': empresa.id,
                'slug': empresa.slug,
                'em_trial': empresa.em_trial,
                'assinatura_ativa': empresa.assinatura_ativa
            }
        }
    }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """
    View para realizar o logout do usuário, invalidando o Refresh Token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from django.core.cache import cache
            from django.utils import timezone
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response({"error": "O campo refresh_token é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            token.blacklist()
            access_token = request.auth
            jti = access_token.get('jti') if access_token else None
            exp = access_token.get('exp') if access_token else None
            if jti and exp:
                timeout = max(1, int(exp - timezone.now().timestamp()))
                cache.set(f'revoked_access:{jti}', True, timeout=timeout)
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Token inválido ou já expirado."}, status=status.HTTP_400_BAD_REQUEST)
