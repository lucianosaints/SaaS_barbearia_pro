#!/bin/sh
set -e

echo "=== Entrypoint: Ajustando permissões de /app/media ==="
mkdir -p /app/media/profissionais
chmod -R 755 /app/media
# Garante que novos arquivos criados sejam legíveis por todos (Nginx)
umask 0022

echo "=== Entrypoint: Executando migrações ==="
python manage.py migrate --noinput

echo "=== Entrypoint: Iniciando servidor ==="
exec "$@"
