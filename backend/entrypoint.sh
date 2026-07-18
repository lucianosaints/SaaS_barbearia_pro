#!/bin/sh

echo "=== Entrypoint: Ajustando permissões de /app/media ==="
mkdir -p /app/media/profissionais
chmod -R 755 /app/media
# Garante que novos arquivos criados sejam legíveis por todos (Nginx)
umask 0022

echo "=== Entrypoint: Executando migrações ==="
python manage.py migrate --noinput || echo "AVISO: Migrate falhou, mas o servidor será iniciado mesmo assim para permitir debug via exec."

echo "=== Entrypoint: Iniciando servidor ==="
exec "$@"
