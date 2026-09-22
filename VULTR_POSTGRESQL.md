# SalaoPro: Vultr e PostgreSQL no mesmo servidor

Confirmado pelo proprietário: Ubuntu na Vultr, site https://www.salaopro.site, com containers barbeiro_pro_frontend, barbeiro_pro_backend, barbeiro_pro_waha e barbeiro_pro_db. O banco usa a imagem postgres:15-alpine, no mesmo servidor. A consulta pública encontrou Nginx e uma API JSON autenticada em https://www.salaopro.site/api/. O Compose foi localizado pelo label do backend em `/root/SaaS_barbearia_pro/docker-compose.yml`. A versão exata do PostgreSQL em execução ainda precisa ser confirmada.

A cópia local do projeto não contém o Compose/Dockerfiles de produção nem a configuração do serviço WAHA. Não substitua a implantação atual por esta pasta sem recuperar e conferir esses arquivos. O compose.test.yml é exclusivo de testes.

O conteúdo dos dois Dockerfiles foi recebido e registrado em `deploy/references/`. O frontend usa Node 20, npm install, Nginx com workers root e mídia compartilhada em `/app/media/profissionais`. A proposta em `deploy/FRONTEND_BUILD.md` atualiza o build para Node 22 e npm ci. O backend usa Python 3.11, collectstatic no build, mídia com chmod 777 e Gunicorn com três workers. O entrypoint é copiado para fora de /app porque esse diretório recebe bind mount.

Gunicorn foi acrescentado aos requisitos locais para Unix, com versão candidata 26.2.0 no lock; não foi executado no Windows nem implantado no servidor. O entrypoint recebido ignora falhas de migração e não coleta estáticos depois do bind mount. Foi preparada uma versão local corrigida em backend/entrypoint.sh, documentada em deploy/BACKEND_BUILD.md. Falta conferir versão atual do Gunicorn, nginx.conf e os serviços/volumes do Compose antes de aplicar as propostas.

O usuário postgres não existir no Ubuntu é compatível com essa instalação: o PostgreSQL está no container. Para confirmar a versão e consultar a estrutura da implantação, execute um comando de cada vez:

```sh
docker exec barbeiro_pro_db sh -c 'psql -X -w -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-postgres}" -Atc "SHOW server_version;"'
docker compose -f /root/SaaS_barbearia_pro/docker-compose.yml config --services
find /root/SaaS_barbearia_pro -maxdepth 3 -type f -iname '*dockerfile*' -print
docker inspect barbeiro_pro_backend --format '{{index .Config.Labels "com.docker.compose.project.working_dir"}}'
```

Esses comandos não imprimem variáveis de ambiente ou senhas. Labels vazios indicam que será necessário localizar o arquivo de implantação por outro meio.

## Primeiro: identificar o ambiente sem modificá-lo

No terminal do servidor, execute o conteúdo de diagnostico_servidor.sh ou, após transferir esse arquivo, execute:

```sh
sh diagnostico_servidor.sh
```

O script mostra apenas nomes de serviços, nomes/imagens de containers e versões. A consulta SQL é SHOW server_version. Não lê arquivos .env, não imprime senhas, não lista registros de clientes, não reinicia serviços e não executa migrações. Se o PostgreSQL estiver em container, a versão poderá ser inferida inicialmente pela imagem e deverá ser confirmada dentro dele depois de identificar seu nome.

O Django 5.2 desta atualização exige PostgreSQL 14 ou superior. Se a versão for anterior, interrompa a publicação desta atualização: será necessário planejar a compatibilidade/atualização do banco separadamente. Não atualize o PostgreSQL automaticamente nem crie um banco vazio no lugar do atual. [Requisito oficial do Django](https://docs.djangoproject.com/en/5.2/ref/databases/#postgresql-notes).

## Variáveis da aplicação

Rede Docker confirmada: `saas_barbearia_pro_barbeiro_pro_net`, compartilhada pelo backend (aliases `backend`, `barbeiro_pro_backend`) e PostgreSQL (aliases `db`, `barbeiro_pro_db`). O exemplo local usa `DB_HOST=db`. O usuário confirmou a configuração efetiva do Django: `ENGINE=django.db.backends.postgresql`, `HOST=db`, `PORT=5432`. Portanto, o endereço configurado usa a rede interna; a publicação de 5432 no host não é necessária para esse caminho. Preparar a alteração do Compose preservando rede e volume, com backup/restauração e janela de manutenção antes de recriar o container.

backend/.env.example já contém os domínios www.salaopro.site e salaopro.site. Copie os valores atuais de DB_NAME, DB_USER, DB_PASSWORD e DJANGO_SECRET_KEY para o mecanismo de configuração do serviço existente. Esses arquivos de exemplo não são carregados automaticamente pelo Django.

- DB_ENGINE deve ser postgresql. A aplicação recusa SQLite em produção.
- Se Django e PostgreSQL executam diretamente no Ubuntu, DB_HOST normalmente será 127.0.0.1 ou o socket já utilizado. Preserve a porta atual; 5432 é somente o padrão do exemplo.
- Se executam em containers, preserve o nome de serviço/host da rede Docker. 127.0.0.1 dentro do container aponta para o próprio container, não para outro serviço.
- DB_SSLMODE=prefer conserva a negociação usada anteriormente pelo projeto para a conexão local. Não enfraqueça uma configuração existente require/verify-full. DB_SSLROOTCERT permite informar a CA quando usada.
- DB_CONNECT_TIMEOUT limita a espera inicial de conexão a 10 segundos. DB_CONN_MAX_AGE é configurável; use 0 se o serviço atual for ASGI e não houver configuração apropriada de pool.
- Não exponha a porta do PostgreSQL à internet apenas para instalar esta atualização. Os testes devem usar banco isolado, sem credenciais de produção.

Como a API responde no mesmo domínio, VITE_API_URL pode ficar vazio no build de produção. Preserve as regras Nginx existentes para /api/, /painel-master/, /estaticos/ e /arquivos/. Não substitua o virtual host inteiro por um exemplo genérico.

DJANGO_TRUST_PROXY só pode ser habilitado após confirmar que o Nginx define X-Forwarded-Proto a partir da conexão recebida, substituindo qualquer valor enviado pelo cliente. Não habilite HSTS para subdomínios/preload apenas para eliminar alertas de check --deploy sem verificar os outros domínios.

## Testes isolados em PostgreSQL

compose.test.yml não monta o banco de produção nem publica a porta do PostgreSQL. Ele cria um PostgreSQL 15 Alpine temporário e um executor Python com credenciais exclusivas de testes, sem herdar DB_HOST/DB_PASSWORD do ambiente de produção.

Em uma máquina de desenvolvimento/homologação com Docker em execução, a partir da raiz:

```sh
docker compose -p salaopro-tests -f compose.test.yml up --abort-on-container-exit --exit-code-from backend-tests
```

Ao terminar, remova exclusivamente os recursos desse projeto de teste:

```sh
docker compose -p salaopro-tests -f compose.test.yml down --volumes
```

A imagem postgres:15-alpine corresponde à família de versão informada em produção. A tag pode receber correções; para reproduzir também o patch exato, confira o identificador da imagem utilizada no servidor. Não execute este compose como substituto do serviço em produção. A senha literal do arquivo é apenas para o banco efêmero de testes.

A configuração do Compose foi validada localmente. A execução real em PostgreSQL ainda está pendente, pois não há PostgreSQL local instalado nem daemon Docker disponível nesta máquina. Testes de configuração não substituem testes de transações no servidor PostgreSQL.

## Backup e atualização

A busca por arquivos com `compose` no nome, até dois níveis em `/root/SaaS_barbearia_pro`, encontrou somente o arquivo atual. O histórico Git existe e a revisão `ca9b786` (2026-07-31) foi consultada com todos os perfis: também não contém `db`, somente backend, frontend e WAHA. A busca com `git log -G` retornou vazia. Seguir pelo levantamento do container ativo para reconstruir uma proposta, conforme `deploy/RECUPERACAO_COMPOSE_BANCO.md`; a próxima consulta verifica imagem e política de reinício. Uma mensagem de commit revelou uma senha do WAHA; não registrar o valor e, caso ainda vigente, planejar sua rotação com os consumidores. Nas próximas consultas Git, mostrar somente hashes/datas, sem mensagens. A existência do histórico não substitui backup dos dados.

**Divergência identificada no Compose:** a saída filtrada de `/root/SaaS_barbearia_pro/docker-compose.yml` lista `backend`, `frontend` e `waha`, mas não `db`, inclusive após consulta com todos os perfis. Os labels do PostgreSQL confirmam projeto `saas_barbearia_pro`, serviço `db`, esse mesmo arquivo e diretório `/root/SaaS_barbearia_pro`. Esses metadados registram a origem na criação do container; o modelo atual não contém a definição do banco. Procurar cópias anteriores e histórico Git para recuperar essa definição e compará-la aos metadados atuais. Não tratar o banco como descartável nem executar `--remove-orphans`, `down` ou limpeza de volumes durante esse levantamento. Não há ainda um Compose completo conferido para aplicar a retirada da porta pública. Referência parcial salva em `deploy/references/compose.filtered.production.json`, que não é um arquivo de implantação.

Portas recebidas em 20/09/2026: PostgreSQL publicado em `0.0.0.0:5432` e `[::]:5432`, frontend em todas as interfaces na porta 3000 e backend somente em `127.0.0.1:8000`. A acessibilidade externa depende dos firewalls ainda não conferidos. Usuário confirmou que somente o sistema acessa o banco, sem clientes externos. Preparar a remoção da publicação de 5432 no Compose, após confirmar DB_HOST e redes para preservar a conexão interna, armazenamento, backup e janela de manutenção. Nenhuma mudança de rede foi aplicada neste levantamento.

Mounts confirmados pelo usuário: backend e frontend compartilham o volume `saas_barbearia_pro_django_media` em `/app/media`, ambos com leitura e escrita. Inclua esse volume no backup e no ensaio de restauração; o dump do banco não contém as fotos. Preserve a identidade desse volume no Compose.

PostgreSQL usa o volume nomeado `saas_barbearia_pro_postgres_data`, driver local, leitura e escrita, montado em `/var/lib/postgresql/data`. A origem informada no host é `/var/lib/docker/volumes/saas_barbearia_pro_postgres_data/_data`. Preserve esse volume ao ajustar a publicação da porta; não remova nem inicialize outro volume em seu lugar. O mount não comprova backup válido. Os procedimentos abaixo continuam necessários antes de publicar.

O backend monta `/root/SaaS_barbearia_pro/backend` diretamente em `/app`. Trocar somente a imagem não troca o código nessa pasta; a atualização e o retorno precisam coordenar a pasta do host, as dependências da imagem e o entrypoint copiado para `/usr/local/bin`. Não sobrescreva a pasta durante o atendimento sem preparar uma janela de atualização e preservar a versão anterior.

Siga ATUALIZACAO_PRODUCAO.md. Antes da manutenção, identifique o nome do banco, o usuário da aplicação e o mecanismo de serviço. Não é necessário compartilhar senhas.

Para essa instalação Docker, depois de confirmar que POSTGRES_DB corresponde ao banco usado pela aplicação, um modelo de backup é:

```sh
# Use um diretório de backup existente e protegido no host. Não use -t no docker exec.
umask 077
docker exec barbeiro_pro_db sh -c 'pg_dump -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:?Confirme o banco da aplicação}" --format=custom' > /caminho/protegido/salaopro-pre-atualizacao.dump
docker exec -i barbeiro_pro_db pg_restore --list < /caminho/protegido/salaopro-pre-atualizacao.dump
```

Confira o código de saída do pg_dump antes de seguir. Listar o arquivo não prova que a restauração funciona: restaure e teste em um banco separado de homologação antes da atualização. Não remova o volume do banco, não recrie o serviço db e preserve o serviço WAHA durante a atualização da aplicação.

Pare as gravações da versão antiga antes de fazer as migrações/publicação. Não misture versões com regras de reserva diferentes. O comando exato de reinício depende do serviço identificado; não execute systemctl restart ou docker compose up sobre nomes presumidos.

Depois da atualização, valide login, cadastro, reserva simultânea, cancelamento, conclusão e financeiro. Preserve a versão anterior e seu ambiente para retorno, sem apagar reservas novas.
