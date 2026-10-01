#!/bin/sh
# Somente leitura: não reinicia serviços, não altera banco e não imprime configurações/segredos.
set -u

printf '\nSistema operacional\n'
if [ -r /etc/os-release ]; then
    . /etc/os-release
    printf '%s\n' "$PRETTY_NAME"
fi

printf '\nServiços em execução (somente nomes)\n'
if command -v systemctl >/dev/null 2>&1; then
    systemctl list-units --type=service --state=running --no-pager --plain --no-legend 2>/dev/null |
        awk '{print $1}'
fi

printf '\nNginx\n'
if command -v nginx >/dev/null 2>&1; then
    nginx -v 2>&1
fi

printf '\nCliente PostgreSQL (pode diferir da versão do servidor)\n'
if command -v psql >/dev/null 2>&1; then
    psql --version
fi

printf '\nVersão do servidor PostgreSQL local\n'
if command -v sudo >/dev/null 2>&1; then
    if ! sudo -n -u postgres psql -X -w -At -d postgres -c 'SHOW server_version;' 2>/dev/null; then
        printf '%s\n' 'Não identificada por conexão local. Pode estar em container ou exigir outra forma de acesso.'
    fi
else
    printf '%s\n' 'Consulta local não disponível com este usuário.'
fi

printf '\nContainers em execução (somente nomes e imagens)\n'
if command -v docker >/dev/null 2>&1; then
    if ! docker ps --format 'table {{.Names}}\t{{.Image}}' 2>/dev/null; then
        printf '%s\n' 'Docker presente, mas o daemon não está acessível com este usuário.'
    fi
else
    printf '%s\n' 'Comando docker não encontrado.'
fi
