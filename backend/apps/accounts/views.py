from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import ScopedRateThrottle
from apps.accounts.models import Usuario
from apps.accounts.serializers import UsuarioSerializer, CustomTokenObtainPairSerializer
from apps.accounts.permissions import IsAdminUserOrReadOnly, IsDemoUserReadOnly
from apps.tenants.permissions import IsEmpresaAtiva
from rest_framework_simplejwt.authentication import JWTAuthentication

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
    authentication_classes = [JWTAuthentication]
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdminUserOrReadOnly, IsEmpresaAtiva, IsDemoUserReadOnly]

    def get_queryset(self):
        user = self.request.user
        print(f"\n=== DEBUG USUARIO VIEWSET ===")
        print(f"USER: {user} | AUTENTICADO: {getattr(user, 'is_authenticated', False)}")
        print(f"HEADER AUTH: {self.request.headers.get('Authorization', 'NENHUM')}")
        
        # Se for rota pública (wizard de agendamento), deve receber o empresa_id via query params
        empresa_id_param = self.request.query_params.get('empresa_id')
        if empresa_id_param:
            print(f"ROTA PÚBLICA - Filtrando estritamente pelo param empresa_id: {empresa_id_param}")
            return Usuario.objects.filter(
                empresa_id=empresa_id_param, 
                tipo__in=['PROFISSIONAL', 'ADMINISTRADOR'], 
                is_active=True,
                is_staff=False,
                is_superuser=False
            )
            
        # Se for rota do painel administrativo (usuário autenticado)
        if user and user.is_authenticated:
            # Se for superusuário, pode ver tudo (opcional)
            if user.is_superuser:
                print("ROTA PRIVADA - Usuário é SUPERUSER. Retornando TODOS os usuários.")
                return Usuario.objects.all()
                
            # Para usuários comuns/administradores da empresa, filtra estritamente pelo ID da empresa deles
            empresa_id = getattr(user, 'empresa_id', None)
            print(f"ROTA PRIVADA - Usuário Autenticado. empresa_id do usuário: {empresa_id}")
            if empresa_id:
                return Usuario.objects.filter(
                    empresa_id=empresa_id,
                    is_staff=False,
                    is_superuser=False
                )
            print("ALERTA: Usuário logado mas sem empresa_id associada!")
            return Usuario.objects.none()
                
        # Caso falte autenticação ou parâmetro, bloqueia o retorno de dados globais
        print("BLOQUEIO: Requisição anônima sem parâmetro de empresa. Retornando NADA.")
        return Usuario.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        empresa_id = self.request.data.get('empresa')
        # Associa automaticamente o novo usuário à empresa do criador e fixa como PROFISSIONAL
        if not empresa_id and user.empresa:
            serializer.save(empresa=user.empresa, tipo='PROFISSIONAL')
        else:
            serializer.save(tipo='PROFISSIONAL')

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
            # Bloqueia a alteração do email
            if 'email' in data:
                del data['email']
            
            serializer = self.get_serializer(usuario, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    whatsapp = request.data.get('whatsapp')

    if not all([nome_barbearia, nome_admin, email, senha, whatsapp]):
        return Response(
            {"error": "Todos os campos são obrigatórios."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if Usuario.objects.filter(username=email).exists() or Usuario.objects.filter(email=email).exists():
        return Response(
            {"error": "Já existe um usuário com este e-mail."},
            status=status.HTTP_400_BAD_REQUEST
        )

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
