from rest_framework import serializers
from apps.accounts.models import Usuario
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo de Usuario customizado.
    Garante o tratamento seguro de senhas e dados LGPD.
    """
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'password',
            'empresa', 'tipo', 'telefone', 'foto', 'avaliacao', 'taxa_comissao',
            'aceitou_termos', 'data_aceite_termos', 'ip_aceite_termos',
            'is_staff', 'is_active', 'date_joined'
        ]
        read_only_fields = [
            'id', 'empresa', 'date_joined', 'data_aceite_termos', 'ip_aceite_termos'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        # O tenant (empresa) do usuário criado será associado automaticamente
        # via viewset, mas mantemos o suporte no serializer.
        usuario = Usuario(**validated_data)
        if password:
            usuario.set_password(password)
        usuario.save()
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


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

