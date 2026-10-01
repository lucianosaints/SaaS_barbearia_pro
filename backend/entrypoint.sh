#!/bin/sh
set -eu

if [ "$#" -eq 0 ]; then
    echo "ERRO: informe o comando do servidor." >&2
    exit 64
fi

# Comandos administrativos explícitos não devem executar migrações implicitamente.
# O CMD de produção chama gunicorn diretamente.
case "${1##*/}" in
    gunicorn|waitress-serve) ;;
    *) exec "$@" ;;
esac

case "${RUN_MIGRATIONS-1}" in
    0|1) ;;
    *) echo "ERRO: RUN_MIGRATIONS deve ser 0 ou 1." >&2; exit 64 ;;
esac

umask 0022
echo "=== Entrypoint: Validando configuração ==="
python manage.py check

media_directory="${MEDIA_DIRECTORY:-/app/media}"
mkdir -p "$media_directory/profissionais"
# Não reescrever recursivamente as permissões de arquivos já existentes no volume.
chmod 755 "$media_directory" "$media_directory/profissionais"

if [ "${RUN_MIGRATIONS-1}" = "1" ]; then
    echo "=== Entrypoint: Executando migrações ==="
    python manage.py migrate --noinput
else
    echo "=== Entrypoint: Verificando migrações pendentes ==="
    python manage.py migrate --check
fi

# Executar após os mounts: /app pode ocultar os estáticos gerados no build.
echo "=== Entrypoint: Coletando arquivos estáticos ==="
python manage.py collectstatic --noinput

echo "=== Entrypoint: Iniciando servidor ==="
exec "$@"
