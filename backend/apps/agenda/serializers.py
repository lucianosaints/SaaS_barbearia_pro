from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from apps.agenda.models import Servico, Agendamento, BloqueioHorario, FilaEspera
from apps.accounts.models import Usuario
from apps.agenda.rules import validate_slot


class ServicoSerializer(serializers.ModelSerializer):
    preco = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0'))
    duracao_minutos = serializers.IntegerField(min_value=1)

    class Meta:
        model = Servico
        fields = ['id', 'empresa', 'nome', 'preco', 'duracao_minutos', 'ativo']
        extra_kwargs = {'empresa': {'required': False}}
        # A validacao automatica de unique_together exige empresa cedo demais;
        # a validacao abaixo associa o tenant autenticado antes de checar duplicatas.
        validators = []

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.is_superuser:
            if attrs.get('empresa', user.empresa) != user.empresa:
                raise serializers.ValidationError({'empresa': 'Empresa inválida.'})
            attrs['empresa'] = user.empresa
        if self.instance and attrs.get('empresa', self.instance.empresa) != self.instance.empresa:
            raise serializers.ValidationError({'empresa': 'Não é permitido transferir um serviço.'})
        if not self.instance and not attrs.get('empresa'):
            raise serializers.ValidationError({'empresa': 'Informe a barbearia.'})
        empresa = attrs.get('empresa', self.instance.empresa if self.instance else None)
        nome = attrs.get('nome', self.instance.nome if self.instance else None)
        duplicates = Servico.objects.filter(empresa=empresa, nome=nome)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if nome and duplicates.exists():
            raise serializers.ValidationError({'nome': 'Ja existe um servico com este nome nesta barbearia.'})
        return attrs


class AgendamentoSerializer(serializers.ModelSerializer):
    servicos = serializers.PrimaryKeyRelatedField(queryset=Servico.objects.all(), many=True, allow_empty=False)
    cliente = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.filter(tipo='CLIENTE', is_active=True), required=False)
    cliente_nome = serializers.SerializerMethodField()
    profissional_nome = serializers.SerializerMethodField()
    empresa_slug = serializers.CharField(source='empresa.slug', read_only=True)
    empresa_nome = serializers.CharField(source='empresa.nome', read_only=True)
    servicos_detalhes = ServicoSerializer(source='servicos', many=True, read_only=True)

    class Meta:
        model = Agendamento
        fields = ['id', 'empresa', 'empresa_slug', 'empresa_nome', 'cliente', 'cliente_nome', 'profissional', 'profissional_nome',
                  'servicos', 'servicos_detalhes', 'data_hora_inicio', 'data_hora_fim', 'status',
                  'observacoes', 'valor_total', 'valor_comissao', 'lucro_liquido', 'status_pagamento', 'metodo_pagamento']
        read_only_fields = ['id', 'empresa', 'data_hora_fim', 'valor_total', 'valor_comissao', 'lucro_liquido']

    def get_cliente_nome(self, obj):
        return obj.cliente.get_full_name() or obj.cliente.username

    def get_profissional_nome(self, obj):
        return obj.profissional.get_full_name() or obj.profissional.username

    def validate(self, attrs):
        user = self.context['request'].user
        if 'servicos' in attrs and len({s.pk for s in attrs['servicos']}) != len(attrs['servicos']):
            raise serializers.ValidationError({'servicos': 'Não repita serviços.'})
        if not self.instance:
            if attrs.get('status', 'PENDENTE') != 'PENDENTE':
                raise serializers.ValidationError({'status': 'Novos agendamentos devem ser pendentes.'})
            if user.tipo == 'CLIENTE' and not user.is_superuser:
                if attrs.get('cliente', user) != user:
                    raise PermissionDenied('Não é permitido agendar para outro cliente.')
                attrs['cliente'] = user
            elif 'cliente' not in attrs:
                raise serializers.ValidationError({'cliente': 'Informe o cliente.'})
        return attrs

    def _check_actor(self, attrs, instance=None):
        user = self.context['request'].user
        profissional = attrs.get('profissional', instance.profissional if instance else None)
        if user.tipo == 'CLIENTE' and not user.is_superuser and user.empresa_id and user.empresa_id != profissional.empresa_id:
            raise PermissionDenied('Cliente vinculado a outra barbearia.')
        if not user.is_superuser and user.tipo != 'CLIENTE':
            if not user.empresa_id or not user.empresa.ativo or profissional.empresa_id != user.empresa_id:
                raise PermissionDenied('Agendamento fora da sua barbearia.')
            if user.tipo == 'PROFISSIONAL' and (profissional.pk != user.pk or (instance and instance.profissional_id != user.pk)):
                raise PermissionDenied('Profissionais só podem alterar a própria agenda.')
            cliente = attrs.get('cliente', instance.cliente if instance else None)
            if cliente and cliente.empresa_id not in (None, user.empresa_id):
                raise PermissionDenied('Cliente vinculado a outra barbearia.')
        if instance and user.tipo == 'CLIENTE' and not user.is_superuser:
            if instance.cliente_id != user.pk or set(attrs) != {'status'} or attrs['status'] != 'CANCELADO':
                raise PermissionDenied('Clientes só podem cancelar os próprios agendamentos.')
            from datetime import timedelta
            limite = instance.empresa.horas_limite_cancelamento
            if instance.data_hora_inicio - timezone.now() < timedelta(hours=limite):
                raise serializers.ValidationError({'status': f'O cancelamento exige {limite} horas de antecedência.'})
            if instance.data_hora_inicio <= timezone.now():
                raise serializers.ValidationError({'status': 'Não é possível cancelar um atendimento já iniciado.'})
        cliente = attrs.get('cliente', instance.cliente if instance else user)
        if not instance and cliente and cliente.status == 'BLOQUEADO':
            raise PermissionDenied('Cliente bloqueado para agendamento automático. Entre em contato com a barbearia.')
        if user.tipo == 'CLIENTE' and not user.is_superuser and attrs.get('status_pagamento', 'PENDENTE') != 'PENDENTE':
            raise PermissionDenied('Somente a equipe pode confirmar pagamentos.')
        return profissional

    @transaction.atomic
    def create(self, validated_data):
        profissional = self._check_actor(validated_data)
        # Serializa reservas inclusive quando a agenda ainda está vazia.
        profissional = Usuario.objects.select_for_update().get(pk=profissional.pk)
        supplied = validated_data.pop('servicos')
        servicos = list(Servico.objects.select_for_update().filter(pk__in=[s.pk for s in supplied]).order_by('pk'))
        if len(servicos) != len(supplied):
            raise serializers.ValidationError({'servicos': 'Um serviço foi removido. Atualize a página.'})
        validated_data['data_hora_fim'] = validate_slot(profissional, servicos, validated_data['data_hora_inicio'])
        validated_data['empresa'] = profissional.empresa
        agendamento = Agendamento.objects.create(**validated_data)
        agendamento.servicos.set(servicos)
        return agendamento

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = Agendamento.objects.select_for_update().get(pk=instance.pk)
        profissional = self._check_actor(validated_data, instance)
        locked = {u.pk: u for u in Usuario.objects.select_for_update().filter(
            pk__in=sorted({instance.profissional_id, profissional.pk})).order_by('pk')}
        profissional = locked[profissional.pk]
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        transitions = {'PENDENTE': {'PENDENTE', 'CONFIRMADO', 'CANCELADO'},
                       'CONFIRMADO': {'CONFIRMADO', 'CONCLUIDO', 'CANCELADO'}}
        if old_status == 'CONCLUIDO' and new_status == old_status and set(validated_data) & {'status_pagamento', 'metodo_pagamento'} and set(validated_data) <= {'status', 'status_pagamento', 'metodo_pagamento'}:
            for key, value in validated_data.items():
                setattr(instance, key, value)
            instance.save(update_fields=list(validated_data))
            return instance
        if old_status not in transitions or new_status not in transitions[old_status]:
            raise serializers.ValidationError({'status': 'Transição de status não permitida.'})
        if new_status != old_status and set(validated_data) - {'status', 'status_pagamento', 'metodo_pagamento'}:
            raise serializers.ValidationError('Altere o status separadamente dos dados da reserva.')
        if profissional.empresa_id != instance.empresa_id:
            raise serializers.ValidationError({'profissional': 'Não é permitido transferir o agendamento de barbearia.'})
        supplied = validated_data.pop('servicos', None)
        changed_schedule = supplied is not None or 'profissional' in validated_data or 'data_hora_inicio' in validated_data
        if changed_schedule:
            selected = supplied if supplied is not None else list(instance.servicos.all())
            services = list(Servico.objects.select_for_update().filter(pk__in=[s.pk for s in selected]).order_by('pk'))
            if len(services) != len(selected):
                raise serializers.ValidationError({'servicos': 'Um serviço foi removido.'})
            validated_data['data_hora_fim'] = validate_slot(profissional, services, validated_data.get('data_hora_inicio', instance.data_hora_inicio), instance.pk)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if new_status == 'CONCLUIDO':
            if instance.data_hora_inicio > timezone.now():
                raise serializers.ValidationError({'status': 'O atendimento ainda não começou.'})
            rate = profissional.taxa_comissao
            if not Decimal('0') <= rate <= Decimal('100'):
                raise serializers.ValidationError({'profissional': 'A comissão deve estar entre 0 e 100%.'})
            total = instance.valor_total
            if total is None:
                total = sum((s.preco for s in instance.servicos.all()), Decimal('0'))
            if total < 0:
                raise serializers.ValidationError('O valor do atendimento não pode ser negativo.')
            instance.valor_total = total
            instance.valor_comissao = (total * rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            instance.lucro_liquido = total - instance.valor_comissao
        instance.save()
        if supplied is not None:
            instance.servicos.set(services)
        return instance

    def to_representation(self, instance):
        # Sobrescreve para retornar os detalhes dos serviços em vez de apenas os IDs no GET
        representation = super().to_representation(instance)
        representation['servicos_detalhes'] = ServicoSerializer(instance.servicos.all(), many=True).data
        
        request = self.context.get('request')
        
        if instance.cliente:
            representation['cliente_nome'] = instance.cliente.get_full_name() or instance.cliente.username
            representation['cliente_telefone'] = instance.cliente.telefone
            
            if instance.cliente.foto:
                url = instance.cliente.foto.url
                representation['cliente_foto'] = request.build_absolute_uri(url) if request else url
            else:
                representation['cliente_foto'] = None
            
        if instance.profissional:
            representation['profissional_nome'] = instance.profissional.get_full_name() or instance.profissional.username
            
            if instance.profissional.foto:
                url = instance.profissional.foto.url
                representation['profissional_foto'] = request.build_absolute_uri(url) if request else url
            else:
                representation['profissional_foto'] = None
            
        if instance.empresa:
            representation['empresa_nome'] = instance.empresa.nome
            representation['empresa_slug'] = instance.empresa.slug
            
        return representation


class BloqueioHorarioSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo BloqueioHorario.
    """
    class Meta:
        model = BloqueioHorario
        fields = ['id', 'empresa', 'profissional', 'data_hora_inicio', 'data_hora_fim', 'motivo']
        read_only_fields = ['id', 'empresa']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.profissional:
            representation['profissional_nome'] = instance.profissional.get_full_name() or instance.profissional.username
        else:
            representation['profissional_nome'] = 'Todos os Profissionais'
        return representation


class FilaEsperaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo FilaEspera.
    """
    class Meta:
        model = FilaEspera
        fields = ['id', 'empresa', 'cliente_nome', 'cliente_telefone', 'data_desejada', 'horario_desejado', 'notificado', 'criado_em']
        read_only_fields = ['id', 'notificado', 'criado_em']
