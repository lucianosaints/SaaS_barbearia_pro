from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import ScopedRateThrottle
from apps.accounts.models import Usuario
from apps.accounts.serializers import UsuarioSerializer, CustomTokenObtainPairSerializer
from apps.accounts.permissions import IsAdminUserOrReadOnly
from apps.tenants.permissions import IsEmpresaAtiva

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    View customizada para obtenção de Token JWT.
    Retorna o perfil do usuário logado no mesmo payload do token.
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de Usuários.
    Garante o isolamento multi-tenant, permitindo listar apenas usuários
    pertencentes à mesma empresa do usuário logado ou filtrar profissionais publicamente.
    """
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdminUserOrReadOnly, IsEmpresaAtiva]

    def get_queryset(self):
        # Filtro de listagem pública por empresa para o Wizard
        empresa_id = self.request.query_params.get('empresa_id')
        if empresa_id:
            return Usuario.objects.filter(empresa_id=empresa_id, tipo='PROFISSIONAL', is_active=True)

        user = self.request.user
        if user.is_authenticated and user.tipo != 'CLIENTE':
            if user.is_superuser:
                return Usuario.objects.all()
            if user.empresa:
                return Usuario.objects.filter(empresa=user.empresa)
            return Usuario.objects.filter(id=user.id)
            
        # Se for consulta anônima ou cliente final logado, lista todos os profissionais ativos no MVP
        return Usuario.objects.filter(tipo='PROFISSIONAL', is_active=True)

    def perform_create(self, serializer):
        user = self.request.user
        empresa_id = self.request.data.get('empresa')
        # Associa automaticamente o novo usuário à empresa do criador e fixa como PROFISSIONAL
        if not empresa_id and user.empresa:
            serializer.save(empresa=user.empresa, tipo='PROFISSIONAL')
        else:
            serializer.save(tipo='PROFISSIONAL')


@api_view(['POST'])
@permission_classes([AllowAny])
def registrar_cliente(request):
    """
    Cadastra um novo cliente no sistema e retorna imediatamente os tokens JWT.
    """
    nome = request.data.get('nome')
    telefone = request.data.get('telefone')
    email = request.data.get('email')
    senha = request.data.get('senha')
    empresa_id = request.data.get('empresa_id')

    if not all([nome, email, senha]):
        return Response(
            {"error": "Os campos Nome, Email e Senha são obrigatórios."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # O username será o email do usuário
    if Usuario.objects.filter(username=email).exists() or Usuario.objects.filter(email=email).exists():
        return Response(
            {"error": "Já existe um usuário cadastrado com este e-mail."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Separa primeiro e último nome
    nomes = nome.strip().split(' ', 1)
    first_name = nomes[0]
    last_name = nomes[1] if len(nomes) > 1 else ''

    # Criação do cliente
    usuario = Usuario(
        username=email,
        email=email,
        first_name=first_name,
        last_name=last_name,
        telefone=telefone,
        tipo='CLIENTE',
        is_active=True
    )

    if empresa_id:
        from apps.tenants.models import Empresa
        empresa = Empresa.objects.filter(id=empresa_id).first()
        if empresa:
            usuario.empresa = empresa

    usuario.set_password(senha)
    usuario.save()

    # Gera os tokens JWT
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
                'id': usuario.empresa.id,
                'slug': usuario.empresa.slug,
                'em_trial': usuario.empresa.em_trial,
                'assinatura_ativa': usuario.empresa.assinatura_ativa
            } if usuario.empresa else None
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def registrar_saas(request):
    """
    Cadastra uma nova barbearia (Empresa) e o usuário administrador.
    Inicia o período de teste grátis (Trial).
    """
    from datetime import timedelta
    from django.utils import timezone
    from django.utils.text import slugify
    from apps.tenants.models import Empresa

    nome_barbearia = request.data.get('nome_barbearia')
    nome_admin = request.data.get('nome_admin')
    email = request.data.get('email')
    senha = request.data.get('senha')

    if not all([nome_barbearia, nome_admin, email, senha]):
        return Response(
            {"error": "Todos os campos são obrigatórios."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if Usuario.objects.filter(username=email).exists() or Usuario.objects.filter(email=email).exists():
        return Response(
            {"error": "Já existe um usuário com este e-mail."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Criar a Empresa com 7 dias de trial
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
        data_fim_trial=timezone.now().date() + timedelta(days=7),
        ativo=True
    )

    # Separa primeiro e último nome
    nomes = nome_admin.strip().split(' ', 1)
    first_name = nomes[0]
    last_name = nomes[1] if len(nomes) > 1 else ''

    # Criar o Usuário Administrador
    usuario = Usuario(
        username=email,
        email=email,
        first_name=first_name,
        last_name=last_name,
        tipo='ADMINISTRADOR',
        is_active=True,
        empresa=empresa
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
