from rest_framework import serializers
from apps.accounts.models import Usuario

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
            'empresa', 'aceitou_termos', 'data_aceite_termos', 'ip_aceite_termos',
            'is_staff', 'is_active', 'date_joined'
        ]
        read_only_fields = [
            'id', 'date_joined', 'data_aceite_termos', 'ip_aceite_termos'
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
