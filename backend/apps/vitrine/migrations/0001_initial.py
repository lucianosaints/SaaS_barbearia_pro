from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [('tenants', '0010_sitevisitcounter')]
    operations = [
        migrations.CreateModel(
            name='Produto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=150)),
                ('descricao', models.TextField(blank=True, default='')),
                ('preco', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('preco_promocional', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('estoque', models.PositiveIntegerField(default=0)),
                ('controlar_estoque', models.BooleanField(default=True)),
                ('disponivel', models.BooleanField(default=True)),
                ('destaque', models.BooleanField(default=False)),
                ('foto', models.ImageField(blank=True, null=True, upload_to='produtos/')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='produtos', to='tenants.empresa')),
            ],
            options={'ordering': ['-destaque', 'nome']},
        ),
        migrations.AddConstraint(
            model_name='produto',
            constraint=models.UniqueConstraint(fields=('empresa', 'nome'), name='produto_nome_unico_por_empresa'),
        ),
    ]
