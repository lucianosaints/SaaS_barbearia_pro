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
        fields = ['id', 'nome', 'first_name', 'last_name', 'empresa', 'tipo']

    def get_nome(self, obj):
        return obj.get_full_name() or 'Profissional'


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False)
    taxa_comissao = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal('0'), max_value=Decimal('100'), required=False)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password',
                  'empresa', 'tipo', 'telefone', 'taxa_comissao', 'aceitou_termos',
                  'data_aceite_termos', 'ip_aceite_termos', 'is_staff', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined', 'is_staff', 'aceitou_termos', 'data_aceite_termos', 'ip_aceite_termos']

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.is_superuser:
            if self.instance and (self.instance.is_superuser or self.instance.is_staff):
                raise serializers.ValidationError('Contas privilegiadas só podem ser alteradas por um superusuário.')
            if attrs.get('empresa', user.empresa) != user.empresa:
                raise serializers.ValidationError({'empresa': 'Empresa inválida.'})
            attrs['empresa'] = user.empresa
        if self.instance and attrs.get('empresa', self.instance.empresa) != self.instance.empresa:
            raise serializers.ValidationError({'empresa': 'Não é permitido transferir usuários com histórico.'})
        if not self.instance and not attrs.get('password'):
            raise serializers.ValidationError({'password': 'Informe uma senha.'})
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
    empresa_id = serializers.IntegerField(required=False, min_value=1)

    def validate_email(self, value):
        value = value.strip().lower()
        if Usuario.objects.filter(email__iexact=value).exists() or Usuario.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Já existe um usuário com este e-mail.')
        return value

    def validate(self, attrs):
        names = attrs['nome'].split(' ', 1)
        candidate = Usuario(username=attrs['email'], email=attrs['email'], first_name=names[0],
                            last_name=names[1] if len(names) > 1 else '')
        try:
            validate_password(attrs['senha'], candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'senha': exc.messages})
        if 'empresa_id' in attrs:
            from apps.tenants.models import Empresa
            if not Empresa.objects.filter(pk=attrs['empresa_id'], ativo=True).exists():
                raise serializers.ValidationError({'empresa_id': 'Barbearia inválida.'})
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id, 'nome': self.user.get_full_name() or self.user.username,
            'email': self.user.email, 'tipo': self.user.tipo
        }
        return data
