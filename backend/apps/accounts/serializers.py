from decimal import Decimal
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.accounts.models import Usuario


class ProfissionalPublicoSerializer(serializers.ModelSerializer):
    nome = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'nome', 'first_name', 'last_name', 'empresa', 'tipo', 'foto', 'avaliacao']

    def get_nome(self, obj):
        return obj.get_full_name() or 'Profissional'


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True, trim_whitespace=False)
    foto = serializers.ImageField(required=False, allow_null=True)
    comissao_percentual = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0'), max_value=Decimal('100'), required=False)
    taxa_comissao = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0'), max_value=Decimal('100'), required=False)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password',
                  'empresa', 'tipo', 'status', 'telefone', 'foto', 'avaliacao', 'comissao_percentual', 'taxa_comissao', 'aceitou_termos',
                  'data_aceite_termos', 'ip_aceite_termos', 'is_staff', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'is_staff', 'aceitou_termos', 'data_aceite_termos', 'ip_aceite_termos']

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.is_superuser:
            if self.instance and self.instance.pk != user.pk and (self.instance.is_superuser or self.instance.is_staff):
                raise serializers.ValidationError('Contas privilegiadas só podem ser alteradas por um superusuário.')
            if attrs.get('empresa', user.empresa) != user.empresa:
                raise serializers.ValidationError({'empresa': 'Empresa inválida.'})
            attrs['empresa'] = user.empresa
            if not self.instance:
                attrs.setdefault('tipo', 'PROFISSIONAL')
        if self.instance and attrs.get('empresa', self.instance.empresa) != self.instance.empresa:
            raise serializers.ValidationError({'empresa': 'Não é permitido transferir usuários com histórico.'})
        if not self.instance and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'Informe uma senha.'})
        if self.instance and not attrs.get('password'):
            attrs.pop('password', None)
        if 'password' in attrs:
            candidate = Usuario(username=attrs.get('username', getattr(self.instance, 'username', '')),
                                email=attrs.get('email', getattr(self.instance, 'email', '')))
            try:
                validate_password(attrs['password'], candidate)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({'password': exc.messages})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        return Usuario.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RegistroClienteSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=150)
    senha = serializers.CharField(write_only=True, trim_whitespace=False)
    telefone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    empresa_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        names = attrs['nome'].split(' ', 1)
        candidate = Usuario(username=attrs['email'], email=attrs['email'], first_name=names[0],
                            last_name=names[1] if len(names) > 1 else '')
        try:
            validate_password(attrs['senha'], candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'senha': exc.messages})
        if Usuario.objects.filter(email__iexact=attrs['email']).exists() or Usuario.objects.filter(username__iexact=attrs['email']).exists():
            raise serializers.ValidationError({'detail': 'Não foi possível concluir o cadastro. Verifique os dados informados.'})
        if attrs.get('empresa_id') is not None:
            from apps.tenants.models import Empresa
            if not Empresa.objects.filter(pk=attrs['empresa_id'], ativo=True).exists():
                raise serializers.ValidationError({'empresa_id': 'Barbearia inválida.'})
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer customizado para injetar dados do perfil do usuário no retorno de autenticação.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'nome': self.user.get_full_name() or self.user.username,
            'email': self.user.email,
            'tipo': self.user.tipo,
            'empresa': {
                'id': self.user.empresa_id,
                'nome': self.user.empresa.nome if self.user.empresa else None,
                'slug': self.user.empresa.slug if self.user.empresa else None,
                'em_trial': self.user.empresa.em_trial if self.user.empresa else False,
                'assinatura_ativa': self.user.empresa.assinatura_ativa if self.user.empresa else False,
            } if self.user.empresa else None
        }
        return data
