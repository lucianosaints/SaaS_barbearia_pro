#!/bin/sh
# Referência recebida do usuário em 20/09/2026; não executar como script local.
# Origem: /root/SaaS_barbearia_pro/backend/entrypoint.sh.

echo "=== Entrypoint: Ajustando permissões de /app/media ==="
mkdir -p /app/media/profissionais
chmod -R 755 /app/media
umask 0022

echo "=== Entrypoint: Executando migrações ==="
python manage.py migrate --noinput || echo "AVISO: Migrate falhou, mas o servidor será iniciado mesmo assim para permitir debug via exec."

echo "=== Entrypoint: Iniciando servidor ==="
exec "$@"
