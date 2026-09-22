# Compatibilidade do backend Docker

O Dockerfile recebido está registrado em `references/backend.Dockerfile.production`. A imagem Python 3.11 é compatível com a versão local do projeto. O entrypoint de produção também foi recebido, salvo em `references/backend.entrypoint.production.sh` e corrigido localmente em `backend/entrypoint.sh`. Ainda falta conferir o Compose e os volumes antes de definir o Dockerfile final.

## Dependências

O comando de produção usa Gunicorn com três workers. Gunicorn foi acrescentado aos requisitos e ao lock local, com marcador que o ignora no Windows. A versão candidata é 26.2.0; a resolução pelo pip encontrou somente esse pacote, sem novas dependências obrigatórias. A versão atualmente instalada no servidor ainda não foi consultada. A candidata precisa ser testada em Linux/homologação antes da publicação.

[Pacote oficial Gunicorn 26.2.0](https://pypi.org/project/gunicorn/26.2.0/). O teste de resolução de dependências não comprova inicialização do servidor WSGI.

Na proposta de Dockerfile, usar o lock versionado:

```dockerfile
COPY requirements.lock /app/
RUN pip install --no-cache-dir -r requirements.lock
```

Preservar no lock a linha condicional do Gunicorn ao atualizar dependências no Windows; um pip freeze local sozinho não incluirá esse pacote Unix.

## Coleta de estáticos

O comando original `RUN python manage.py collectstatic --noinput` importa as configurações durante o build. Com as validações novas, o build sem variáveis de produção falharia por falta de chave, hosts e configuração PostgreSQL.

O entrypoint novo coleta estáticos na inicialização, depois dos mounts, com a configuração de runtime. Ao integrá-lo ao Dockerfile, remover o `RUN python manage.py collectstatic --noinput` original. Se houver motivo para manter uma coleta adicional durante o build, usar variáveis somente para esse comando, sem gravar DEBUG=True no ambiente final da imagem:

```dockerfile
RUN DJANGO_DEBUG=True DB_ENGINE=sqlite python manage.py collectstatic --noinput
```

Isso não conecta ao PostgreSQL de produção nem exige suas credenciais. O runtime continua exigindo DEBUG=False e a configuração completa de produção. Uma simulação local com `--dry-run` verifica a importação e a seleção dos estáticos, mas não equivale ao build Docker.

O Dockerfile informa que /app recebe bind mount. Esse mount pode esconder tanto os arquivos coletados durante o build quanto o código copiado para a imagem. O entrypoint original não coleta estáticos; a versão nova faz isso depois de montar o volume. Ainda precisamos conferir qual diretório/volume o Nginx serve. Não considerar apenas reconstruir a imagem suficiente para atualizar uma aplicação cujo código vem do host.

## Entry point e mídia

O script é copiado para /usr/local/bin/entrypoint.sh para permanecer disponível depois de montar /app. O original executa migrate seguido de `|| echo`, ignorando erros e iniciando o servidor mesmo se o esquema estiver incompatível. Ele também executa chmod recursivo 755 sobre toda a mídia.

A versão local nova usa `set -eu`, valida a configuração, interrompe em falhas de migração/estáticos e só então executa o servidor com `exec`. Mantém umask 0022 e permissões 755 nos diretórios principais, sem reescrever recursivamente os arquivos existentes.

`RUN_MIGRATIONS=1` é o padrão e mantém o comportamento de migrar na inicialização do único backend, agora sem ignorar falhas. Para um deploy com migração executada separadamente ou múltiplos containers, usar `RUN_MIGRATIONS=0`: o script faz `migrate --check` e recusa iniciar caso falte alguma migração. Não iniciar simultaneamente vários containers com migrações automáticas habilitadas.

A inicialização automática ocorre apenas para o comando direto `gunicorn` ou `waitress-serve`. Comandos administrativos explícitos, por exemplo `python manage.py migrate --plan`, são executados diretamente, sem aplicar migrações por surpresa. Manter o CMD direto do Dockerfile; não envolvê-lo em `sh -c` sem revisar essa detecção.

Esse comportamento foi preparado localmente. O entrypoint antigo copiado para /usr/local/bin dentro da imagem não muda apenas por atualizar o arquivo no bind mount: a implantação precisa reconstruir a imagem e recriar somente os serviços pertinentes depois dos backups e da homologação.

Validação: oito testes shell passaram com Python/Gunicorn simulados, verificando sequência, interrupção em falhas e comandos administrativos sem migração implícita. Executados via Git Bash no Windows; isso não equivale a validar a imagem Linux ou o banco PostgreSQL de produção.

Enquanto a imagem antiga estiver em uso, `docker compose run backend ...` pode executar migrações antes do comando solicitado, inclusive se ele for somente uma consulta. Não utilizá-lo para diagnóstico sem revisar/substituir explicitamente o entrypoint. `docker exec` em um container já em execução não reexecuta o entrypoint.

O Dockerfile original concede 777 a /app/media, e o frontend usa workers Nginx root para ler mídia compartilhada. Não foi aplicada alteração nessas permissões. A proposta final deve considerar proprietários, UID/GID e volumes reais para preservar acesso às imagens sem manter permissões abertas desnecessárias.

Por ora, preserve a configuração existente de três workers. Não trocar Gunicorn por Waitress no servidor apenas porque Waitress está disponível no ambiente Windows local.

Próximas consultas somente leitura no servidor:

```sh
docker exec barbeiro_pro_backend gunicorn --version
cat /root/SaaS_barbearia_pro/frontend/nginx.conf
```

Não aplicar comandos de publicação até conferir também nginx.conf, nomes dos serviços, volumes e diferenças entre o código local e o código em produção.
