from django.db import migrations, models


def create_counter(apps, schema_editor):
    counter = apps.get_model('tenants', 'SiteVisitCounter')
    counter.objects.get_or_create(pk=1, defaults={'total': 0})


class Migration(migrations.Migration):
    dependencies = [('tenants', '0009_merge_20260721_0129')]

    operations = [
        migrations.CreateModel(
            name='SiteVisitCounter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total', models.PositiveBigIntegerField(default=0)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Contador de visitas do site',
                'verbose_name_plural': 'Contador de visitas do site',
            },
        ),
        migrations.RunPython(create_counter, migrations.RunPython.noop),
    ]
