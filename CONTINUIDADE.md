# Continuidade — Barbeiro Pro / SalaoPro

Atualizado em 20/09/2026. Este arquivo registra o estado do trabalho para retomar a atualização com segurança. Não contém senhas ou tokens.

## Objetivo e situação atual

O usuário solicitou análise das regras de negócio, instalação das dependências e correções para preparar uma atualização do sistema já em produção. As alterações foram feitas no projeto local. Não houve publicação, migração ou alteração de dados em produção.

Projeto: `C:\Users\lucia\Desktop\BARBEIRO_PRO\SaaS_barbearia_pro`.

Há arquivos modificados e novos no diretório de trabalho, ainda sem commit criado nesta sessão. Não descartar essas alterações nem substituir arquivos por versões antigas. O usuário pediu explicitamente para salvar o progresso neste arquivo e continuar.

## Produção identificada

- Provedor: Vultr; painel https://console.vultr.com.
- Site: https://www.salaopro.site.
- Servidor informado pelo usuário: Ubuntu 26.04 LTS, hostname `barbearia-app`, IP `140.82.30.186`.
- Aplicação e banco no mesmo servidor, em Docker.
- Compose de produção confirmado pelo label do backend: `/root/SaaS_barbearia_pro/docker-compose.yml`.
- Dockerfiles localizados pelo usuário no servidor: `/root/SaaS_barbearia_pro/backend/Dockerfile` e `/root/SaaS_barbearia_pro/frontend/Dockerfile`. Conteúdo de ambos recebido e salvo como referência em `deploy/references/`.
- Consulta pública: página inicial HTTP 200, Nginx; `/api/` HTTP 401 JSON com autenticação Bearer.

Containers informados pelo usuário:

| Container | Imagem |
| --- | --- |
| `barbeiro_pro_frontend` | `saas_barbearia_pro-frontend` |
| `barbeiro_pro_backend` | `saas_barbearia_pro-backend` |
| `barbeiro_pro_waha` | `devlikeapro/waha:chrome` |
| `barbeiro_pro_db` | `postgres:15-alpine` |

A imagem indica PostgreSQL 15, compatível com Django 5.2. O patch exato em execução ainda não foi consultado. O comando `sudo -u postgres ...` no host falhou porque esse usuário não existe no Ubuntu; as consultas devem ocorrer dentro do container do banco.

**A cópia local não contém os Dockerfiles/Compose de produção nem a configuração WAHA.** O único Compose local é de testes. Recuperar e comparar a implantação existente antes de preparar comandos de atualização. Não substituir o Compose atual por `compose.test.yml`.

O usuário não sabe os detalhes de execução do servidor. Orientar com comandos curtos, um de cada vez. Não pedir senhas nem solicitar a impressão integral de `.env`, `docker inspect` ou `docker compose config`, que podem revelar credenciais.

### Dockerfile frontend recebido

Referência funcional salva em `deploy/references/frontend.Dockerfile.production` (instruções recebidas, comentários resumidos). O arquivo usa build com `node:20-alpine`, `npm install`, `VITE_API_URL=/`, Nginx Alpine, configuração externa `nginx.conf`, workers Nginx alterados para root e diretório `/app/media/profissionais` para volume compartilhado com Django.

O frontend local declara Node >=22.12.0 e contém lockfile atualizado. Foi preparado `deploy/FRONTEND_BUILD.md` com as substituições propostas: usar `node:22-alpine`, exigir o lockfile e executar `npm ci`. É uma proposta local para revisão, não foi aplicada ao servidor nem testada em build Docker. A configuração Nginx e o backend ainda precisam ser conferidos antes de integrar essas alterações à implantação.

O Dockerfile existente usa root por motivo declarado de acesso ao volume de mídia. Conferir permissões/UIDs do volume antes de alterar isso; não presumir que remover a instrução preservará as imagens dos profissionais. O local atualmente não possui `frontend/nginx.conf`, configuração de mídia equivalente nem integração WAHA visível, o que exige comparar o código de produção antes de substituir a aplicação.

### Dockerfile backend recebido

Referência em `deploy/references/backend.Dockerfile.production`: Python 3.11-slim, libpq-dev/gcc, instalação de requirements.txt, código em /app, mídia em /app/media/profissionais com chmod 777 e collectstatic durante o build. Copia entrypoint.sh para /usr/local/bin porque o comentário informa que /app é sobrescrito por bind mount. Inicia Gunicorn em 0.0.0.0:8000 com três workers.

Gunicorn estava ausente dos requisitos locais. Foi incluído como dependência Unix, fixado em 26.2.0 no lock, com marcador `sys_platform != "win32"`. A versão atualmente instalada no servidor ainda é desconhecida; a candidata precisa de homologação Linux antes da publicação. A resolução pip da candidata foi verificada; não há novas dependências obrigatórias. `pip check` passou e a instalação simulada do lock no Windows ignora corretamente Gunicorn.

Foi criado `deploy/BACKEND_BUILD.md` com as mudanças propostas. O collectstatic original falharia no build sem as novas variáveis obrigatórias de produção. Foi validada uma simulação com `DJANGO_DEBUG=True DB_ENGINE=sqlite` somente no comando de coleta; não definir DEBUG=True como ENV permanente da imagem. O bind mount pode esconder estáticos/código construídos na imagem, portanto o entrypoint/volumes precisam ser lidos antes de decidir a coleta e publicação finais. Nenhum Dockerfile de produção foi alterado remotamente.

O entrypoint foi recebido e salvo em `deploy/references/backend.entrypoint.production.sh`. Confirmado: mkdir de mídia, chmod recursivo 755, umask 0022, migrate com `|| echo` que ignora falhas, e exec do servidor. Não há coleta de estáticos no script original.

Foi criado `backend/entrypoint.sh` corrigido: `set -eu`, validação de configuração, interrupção se migrações ou collectstatic falharem e coleta de estáticos depois dos mounts. Diretórios principais recebem 755 sem chmod recursivo dos arquivos existentes. RUN_MIGRATIONS=1 mantém migração automática por padrão; RUN_MIGRATIONS=0 somente verifica se há migrações pendentes antes de iniciar. Comandos administrativos explícitos não aplicam migrações implicitamente. A integração com o Dockerfile final depende do Compose e nginx.conf ainda pendentes; remover a coleta obrigatória do build ao usar a coleta de runtime. Nenhuma mudança foi aplicada no servidor.

## Trabalho já realizado

### Dependências e ferramentas

- Ambiente Python local `.venv` criado; dependências instaladas e fixadas em `backend/requirements.lock`.
- Django 5.2.17, DRF 3.16.1, SimpleJWT 5.5.1, psycopg/psycopg-binary 3.3.6, Waitress e WhiteNoise, entre outras dependências do lock.
- Dependências frontend instaladas; Vite atualizado para 7.3.6, ferramentas ESLint/Vitest adicionadas e vulnerabilidades reportadas pelo npm corrigidas.
- Node local observado: 24.13.1; projeto declara Node >=22.12.0. Python local: 3.11.0.
- No PowerShell, usar `npm.cmd`; `npm.ps1` é bloqueado pela política de execução. Usar o executável Python da `.venv` diretamente dispensa ativação.

### Backend

- Escritas de usuários/serviços exigem administrador autorizado; proteção contra acesso cruzado por empresa.
- Catálogo público de profissionais sem e-mail, senha, comissão ou campos administrativos.
- Cadastro com validação de senha, e-mail e limite de tentativas, inclusive para chamadores autenticados.
- Regras compartilhadas de disponibilidade e gravação em `backend/apps/agenda/rules.py`.
- Reserva transacional: profissional e serviços válidos, mesma empresa, empresa ativa, horário futuro, expediente, almoço e conflitos.
- Bloqueio da linha do profissional para serializar reservas no PostgreSQL; SQLite de desenvolvimento utiliza transação IMMEDIATE.
- Recalcular término quando o início/serviços mudam.
- Transições controladas e preservação dos valores financeiros depois da conclusão, com Decimal e arredondamento de centavos.
- Notificação depois do commit, já com os serviços; falha SMTP não desfaz a reserva.
- Blacklist de refresh tokens habilitada; migrações desse aplicativo serão necessárias na implantação.
- Auditoria somente leitura: `python manage.py auditar_agenda --fail-on-issues`.
- Django admin reservado a superusuários globais, sem exclusão de histórico; agendamentos somente para consulta nessa interface.
- Produção exige PostgreSQL explicitamente configurado e recusa fallback para SQLite. DEBUG desligado por padrão, chave segura e hosts explícitos obrigatórios.
- Configuração de conexão PostgreSQL com timeout, verificação de conexão, tempo de reutilização e certificado TLS opcional.

### Frontend

- Renovação de sessão usa a origem configurada, com fila para requisições concorrentes; tratamento de expiração/logout corrigido.
- Seleção evita misturar serviços/profissionais de empresas diferentes; alterações invalidam o horário escolhido.
- Cancelamento de consultas de disponibilidade obsoletas e horário com fuso de São Paulo.
- Ações Confirmar, Concluir e Cancelar no painel, respeitando o perfil.
- Exibição de status e valores financeiros registrados nos painéis; erros de validação mais claros.
- Exemplos de configuração adaptados para `salaopro.site`, com API no mesmo domínio.

## Mudanças de comportamento que precisam ser conferidas na operação

- Cliente só cancela reserva própria antes do início.
- Profissional altera somente seus próprios atendimentos; administrador opera a agenda da empresa.
- Fluxo: PENDENTE → CONFIRMADO ou CANCELADO; CONFIRMADO → CONCLUIDO ou CANCELADO.
- CONCLUIDO e CANCELADO são finais. Conclusão exige que o atendimento já tenha começado.
- Exclusão comum por API desabilitada: desativar cadastros preserva o histórico.
- Comissão padrão continua em 40%, com taxa individual entre 0 e 100%. O campo chamado lucro líquido continua sendo total menos comissão, sem dedução de outras despesas.
- Scripts com acesso direto ao ORM/SQL podem contornar validações da API; não foi criada constraint de exclusão de intervalos no PostgreSQL.

Essas restrições foram implementadas durante o reforço do sistema; o usuário ainda não confirmou sua adequação aos fluxos reais de produção. Estão documentadas para revisão antes da publicação.

## Verificações realizadas e limites

- Última execução do backend: **30 testes aprovados**, incluindo seis testes de configuração do banco.
- Depois dessa execução, **oito testes adicionais do entrypoint passaram**, em execução separada (`python -m unittest discover -s backend/core -p test_entrypoint.py -v`). Usam Git Bash no Windows e comandos Python/Gunicorn simulados, sem banco ou servidor reais. Verificam ordem de inicialização, bloqueio em falhas, controle RUN_MIGRATIONS e ausência de migrações implícitas em comandos administrativos. A primeira tentativa no ambiente restrito falhou por permissão do mkdir; a mesma suíte passou com a permissão de execução necessária.
- Frontend: **6 testes aprovados**, lint e build aprovados na etapa anterior; nenhum código frontend mudou depois dessa verificação.
- `pip check`: sem incompatibilidades. `npm audit`: sem vulnerabilidades reportadas na execução realizada.
- `check --deploy`: aprovado com variáveis de produção de teste; esse comando não comprovou conexão com o banco real.
- Checagem de migrações dos modelos de negócio: sem alterações pendentes. Novas tabelas esperadas: aplicativo JWT `token_blacklist`.
- `git diff --check`: aprovado.
- Teste de concorrência executado em SQLite em arquivo: duas requisições ao mesmo horário resultaram em uma reserva aceita e outra recusada.
- **A suíte ainda não foi executada em PostgreSQL.** Não há PostgreSQL local instalado e o daemon Docker local não estava disponível.
- `compose.test.yml` está configurado com PostgreSQL **15 Alpine**, isolado e sem porta de banco publicada. `docker compose ... config --quiet` validou a configuração; isso não significa que os containers/testes foram executados.
- Build gerado em `frontend/dist`; aviso de bundle de aproximadamente 757 kB (232 kB comprimido), sem impedir a geração.
- Proxy, SMTP real, backup/restauração e compatibilidade com os dados de produção continuam pendentes de homologação.

## Documentos e arquivos de apoio

- [ATUALIZACAO_PRODUCAO.md](ATUALIZACAO_PRODUCAO.md): implantação, restrições, migrações, backup e retorno.
- [VULTR_POSTGRESQL.md](VULTR_POSTGRESQL.md): cenário do servidor, Docker/PostgreSQL e diagnóstico.
- [backend/.env.example](backend/.env.example) e [frontend/.env.example](frontend/.env.example): exemplos; não são carregados automaticamente pelo Django.
- [compose.test.yml](compose.test.yml): ambiente isolado de testes; não é o Compose de produção.
- [diagnostico_servidor.sh](diagnostico_servidor.sh): consultas de diagnóstico sem imprimir configurações/segredos.
- `.gitattributes`: scripts shell com final de linha LF.
- `deploy/references/`: instruções dos dois Dockerfiles recebidos do servidor, salvas como referência.
- `deploy/FRONTEND_BUILD.md` e `deploy/BACKEND_BUILD.md`: propostas de compatibilidade para o build, ainda não aplicadas em produção.
- `backend/entrypoint.sh` e `backend/core/test_entrypoint.py`: inicialização corrigida e seus testes; o original recebido está em `deploy/references/backend.entrypoint.production.sh`.

## Nginx recebido e compatibilidade local (20/09/2026)

- Referência salva em `deploy/references/frontend.nginx.production.conf`; detalhes e pendências em `deploy/NGINX_COMPATIBILIDADE.md`.
- Produção encaminha admin por `/painel-master/`, estáticos por `/estaticos/` e mídia por `/arquivos/`, com alias para `/app/media/` e fallback para Django.
- Settings/URLs locais agora usam esses caminhos com DEBUG=False; desenvolvimento mantém `/admin/` e `/static/`. MEDIA_DIRECTORY configura a pasta de mídia tanto no Django quanto no entrypoint.
- Isso não implementa as funcionalidades de fotos existentes somente em produção, nem o fallback de mídia. Ainda é necessário comparar o código publicado e os volumes.
- API/admin recebem cabeçalho HTTPS fixo, mas estáticos/fallback não. Conferir o proxy externo e as portas antes de definir a configuração final de confiança e redirecionamento.
- Validação desta etapa: 8 testes de configuração e resolução/reversão de URLs passaram; `git diff --check` passou. Não houve build Nginx, teste PostgreSQL ou alteração em produção.

## Volumes confirmados (20/09/2026)

- Backend: bind mount `/root/SaaS_barbearia_pro/backend` → `/app`, leitura e escrita. O código dessa pasta do servidor sobrepõe o código copiado para `/app` na imagem. O pacote de atualização deve considerar tanto a imagem quanto essa pasta; trocar somente a imagem não garante atualizar o código executado.
- Backend e frontend: mesmo volume nomeado `saas_barbearia_pro_django_media` → `/app/media`, leitura e escrita em ambos. Origem informada: `/var/lib/docker/volumes/saas_barbearia_pro_django_media/_data`.
- Preservar esse volume e incluir seu conteúdo no backup/restauração. O dump do PostgreSQL não inclui fotos. Não trocar o nome do projeto/volume sem mapear explicitamente o volume existente.
- O mount confirma o compartilhamento, mas não comprova conteúdo, permissões dos arquivos ou existência de backup. Considerar mount somente leitura no frontend na proposta final, após conferir o Compose.
- Não houve alteração em produção nesta etapa; foram atualizados apenas documentos locais.

## Envio solicitado para develop (20/09/2026)

O usuário pediu envio para `https://github.com/lucianosaints/SaaS_barbearia_pro.git`, branch `develop`. Após fetch, a base local `main` está 145 commits atrás de `origin/develop` (sem commits exclusivos locais antes do registro destas alterações). O remoto já contém WhatsApp, pagamentos, fidelidade, bloqueios, migrações e outras funções ausentes na prévia local. Não substituir esses arquivos silenciosamente nem usar force push.

Foi solicitada a escolha entre integrar preservando as funções atuais (recomendado) ou substituir expressamente pelo conteúdo local. Enquanto isso, preparar um commit local de preservação. Banco de demonstração, logs, ambientes virtuais e dependências instaladas ficam fora do Git. A prévia permanece na cópia local; qualquer integração deve usar diretório separado para não alterar o sistema em execução.

## Prévia local solicitada pelo usuário (20/09/2026)

O usuário pediu para pausar o diagnóstico de produção e rodar a aplicação para visualização. Backend iniciado em `http://127.0.0.1:8000` e frontend em `http://127.0.0.1:3000`, somente no loopback. Banco separado `backend/preview.sqlite3`, com DEBUG=True, DB_ENGINE=sqlite, e-mail no console e dados fictícios do seed (uma empresa, três serviços, dois profissionais). Criado administrador de demonstração `admin.demo`; credencial de teste entregue na conversa. Nenhum acesso ao PostgreSQL de produção foi feito.

Verificações: frontend e módulo App.jsx responderam HTTP 200; login JWT do administrador funcionou; API retornou os três serviços. Não houve inspeção visual: a ferramenta informou que não há navegador disponível. A prévia não substitui homologação no PostgreSQL nem inclui automaticamente funcionalidades presentes somente na cópia de produção.

Processos iniciados ocultos nesta sessão: backend PID 10368, frontend PID 11968. Verificar identidade/processo antes de usar esses PIDs futuramente. Logs em `backend/preview-backend*.log` e `frontend/preview-frontend*.log`. O Vite precisou ser iniciado fora do ambiente restrito após erro de leitura do esbuild; a execução autorizada iniciou normalmente. SQLite e logs já são ignorados pelo Git. O diagnóstico abaixo permanece pendente para depois da revisão local.

## Diagnóstico de produção pausado — próximos passos registrados

### Portas confirmadas (20/09/2026)

- Frontend: porta 80 do container publicada na porta 3000 do host, em `0.0.0.0` e `::`.
- Backend: porta 8000 publicada somente em `127.0.0.1:8000`.
- PostgreSQL: porta 5432 publicada na porta 5432 do host, em `0.0.0.0` e `::`.
- As vinculações do frontend e banco abrangem todas as interfaces IPv4/IPv6. Isso não comprova acesso efetivo pela internet; firewalls e demais controles ainda não foram conferidos. Não afirmar que o banco foi invadido ou que permite acesso sem autenticação.
- Usuário confirmou: somente o sistema acessa o PostgreSQL; não há clientes externos. Preparar a remoção da publicação da porta 5432 no Compose, mantendo a conexão interna entre backend e banco. Antes de aplicar, conferir DB_HOST, redes compartilhadas, armazenamento, backup e janela de manutenção.
- Preparar a restrição de publicação do banco conforme os acessos necessários e conferir se o frontend deve ser acessível somente pelo proxy do host. A configuração efetiva desse proxy ainda não foi recebida.
- Somente documentação local alterada nesta etapa; nenhum comando de alteração executado no servidor.

### Consultas seguintes

PostgreSQL: mount confirmado em 20/09/2026. Volume nomeado `saas_barbearia_pro_postgres_data`, driver local, leitura e escrita, montado em `/var/lib/postgresql/data`; origem no host `/var/lib/docker/volumes/saas_barbearia_pro_postgres_data/_data`. Preservar esse volume ao ajustar o Compose. A existência do volume não comprova backup nem restauração; o dump lógico e o ensaio em banco separado continuam pendentes.

Rede confirmada em 20/09/2026: backend e PostgreSQL compartilham `saas_barbearia_pro_barbeiro_pro_net`. Aliases do backend: `barbeiro_pro_backend`, `backend`; aliases do banco: `barbeiro_pro_db`, `db`. O exemplo local `backend/.env.example` usa `DB_HOST=db`.

Configuração efetiva recebida do Django: `ENGINE=django.db.backends.postgresql`, `HOST=db`, `PORT=5432`. A aplicação está configurada para usar a rede interna, sem depender da porta publicada no host. Preparar a remoção de `ports` do serviço do banco somente após conferir o Compose, backup/restauração e janela de manutenção; a mudança pode recriar o container, preservando o volume existente. Nenhuma alteração remota realizada.

Resumo filtrado do Compose recebido e salvo em `deploy/references/compose.filtered.production.json` (referência incompleta, não usar para implantação). A saída lista somente `backend`, `frontend` e `waha`; **não contém o serviço `db`**, apesar do container PostgreSQL estar em execução. A consulta com todos os perfis em 20/09/2026 retornou o mesmo resultado; a ausência não foi resolvida por `--profile '*'`. Não executar `down`, `--remove-orphans` ou limpeza de volumes durante o diagnóstico. O aviso de `version` obsoleto não impediu a leitura do Compose; sua remoção é secundária.

O resumo confirma os mounts/portas já recebidos de backend/frontend. WAHA declara volume lógico `waha_data` em `/app/.waha`, sem publicação de portas nessa saída; ainda não foi conferido seu mount efetivo nem o nome físico do volume. Todos os três serviços declaram a rede lógica `barbeiro_pro_net`.

Labels do PostgreSQL recebidos: projeto `saas_barbearia_pro`, serviço `db`, arquivo `/root/SaaS_barbearia_pro/docker-compose.yml`, diretório `/root/SaaS_barbearia_pro`. O container registra origem nesse arquivo, mas o modelo atual do Compose, incluindo todos os perfis, não define `db`. O motivo e o momento dessa divergência não foram identificados. Recuperar uma definição anterior ou reconstruir uma proposta a partir dos metadados verificados, preservando credenciais, imagem, volume e rede; não criar um banco novo para substituir o existente.

A busca `find /root/SaaS_barbearia_pro -maxdepth 2 -type f -iname '*compose*' -print` retornou somente `/root/SaaS_barbearia_pro/docker-compose.yml`. Isso não descarta backups em outras pastas ou com outros nomes; nenhuma cópia alternativa foi encontrada no escopo consultado.

Histórico Git recebido: último commit listado para o Compose é `ca9b786` (2026-07-31); anteriores incluem `f2bbd8e`, `a31ad3a`, `6fdbaf2`, `f7198bc`, `0895802`, `3a185a7`, `a5d96c3`, `02f3c26` e `77a5444`. Uma mensagem de commit contém uma senha do WAHA: o valor não foi reproduzido nos documentos. Se ainda estiver vigente, planejar rotação coordenada com a integração. Nas próximas consultas de histórico, omitir `%s` e qualquer mensagem de commit; hashes e datas bastam.

A consulta filtrada da revisão `ca9b786:docker-compose.yml`, incluindo todos os perfis, retornou somente backend, frontend e WAHA, com a mesma estrutura anteriormente recebida. A ausência de `db` também existe nessa revisão; não atribuir a divergência somente a uma edição recente não commitada. Nenhum arquivo do servidor foi restaurado ou alterado.

A busca `git log --all -G '^[[:space:]]+db:'` para `docker-compose.yml` retornou vazia. Isso não comprova que nunca houve definição em outro caminho ou fora do histórico disponível. Não continuar percorrendo commits individualmente sem nova evidência. Seguir pela reconstrução de uma proposta a partir do container ativo, preservando dados e configuração. Plano em `deploy/RECUPERACAO_COMPOSE_BANCO.md`.

Próximo passo: consultar referência e ID da imagem atual, política de reinício, usuário do container e memória compartilhada. Não imprimir variáveis de ambiente, comandos ou healthchecks completos, pois podem conter credenciais. Ainda faltam parâmetros de inicialização, PGDATA efetivo, mecanismo de credenciais preservado no servidor, versão do PostgreSQL e backup/restauração antes de qualquer recriação. Executar um comando de cada vez:

```sh
docker inspect barbeiro_pro_db --format 'image={{.Config.Image}} image_id={{.Image}} restart={{json .HostConfig.RestartPolicy}} user={{json .Config.User}} shm_size={{.HostConfig.ShmSize}}'
```

```sh
docker exec barbeiro_pro_backend gunicorn --version
```

Antes de compartilhar o conteúdo dos arquivos, ocultar eventuais valores de senhas/tokens ou cabeçalhos de autenticação. Não solicitar arquivos `.env`.

Também permanecem pendentes a versão exata do PostgreSQL e o diretório de trabalho registrado pelo Compose:

```sh
docker exec barbeiro_pro_db sh -c 'psql -X -w -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-postgres}" -Atc "SHOW server_version;"'
```

```sh
docker inspect barbeiro_pro_backend --format '{{index .Config.Labels "com.docker.compose.project.working_dir"}}'
```

Essas consultas são somente leitura. Os comandos de metadados mostram versão/caminhos; os comandos `cat` mostram o conteúdo dos Dockerfiles, que deve ser conferido quanto a segredos antes de compartilhar. Se o label de diretório vier vazio, não presumir nomes de serviços ou caminhos adicionais.

Depois de receber as saídas:

1. Localizar e comparar Compose, Dockerfiles, código e configurações usados em produção. Identificar serviços, redes, volumes persistentes e integração WAHA sem revelar segredos.
2. Ajustar os exemplos ao nome real do serviço PostgreSQL na rede Docker; `127.0.0.1` dentro do backend não aponta para outro container.
3. Executar os testes em PostgreSQL 15 isolado e homologar com uma cópia protegida dos dados reais.
4. Conferir novas restrições operacionais, preparar backup/restauração e pacote de atualização mantendo banco e WAHA.
5. Só então definir os comandos exatos de publicação/reinício dos serviços de aplicação e retorno. Não apagar volumes ou recriar o banco. Não executar seed em produção.

## Auditoria e correções de segurança (22/09/2026)

Foi auditada a lista de segurança solicitada e aplicadas correções na cópia integrada `SaaS_barbearia_pro_integracao`. Nenhuma alteração foi feita em produção.

- Rate limit de autenticação agora combina limite por IP (`auth_ip`) e por identidade/conta (`auth_account`), com cache compartilhado configurável para produção.
- CORS permanece em allowlist; origem não autorizada não recebe `Access-Control-Allow-Origin`.
- Rotas públicas de empresa usam `EmpresaPublicaSerializer` e não expõem CNPJ, Pix, beneficiário, vencimentos ou dados administrativos.
- Cadastro de cliente e SaaS usa mensagem genérica quando os dados não podem ser aceitos, evitando confirmação de e-mail existente.
- Access tokens revogados no logout são rejeitados por `RevocableJWTAuthentication`; refresh tokens continuam na blacklist do SimpleJWT.
- Endpoints WAHA exigem administrador da empresa (`IsTenantAdmin`), não apenas autenticação.
- Não foram encontradas consultas SQL cruas nos fluxos auditados; os filtros de agenda mantêm isolamento por empresa/cliente/profissional.

Testes de segurança: 8 aprovados (`apps.accounts.tests_security`). Suíte backend: 60 testes descobertos, 55 aprovados, 1 ignorado e 5 testes do entrypoint aprovados separadamente fora do sandbox por simularem caminhos Unix. Frontend: lint aprovado e 7 testes Vitest aprovados. O build frontend já havia sido aprovado anteriormente; repetir se houver alterações visuais.

Pendências para a próxima sessão: revisar a política de armazenamento de JWT no `localStorage` (avaliar cookie HttpOnly com migração coordenada), confirmar cache Redis/Memcached no Compose de produção e executar uma homologação final com PostgreSQL e proxy reais. Não publicar ainda sem backup e janela de manutenção.

## Verificação de isolamento entre empresas (22/09/2026)

Foi validado o isolamento multiempresa na branch integrada. A suíte cruzada executou 12 testes e todos passaram (`tests_cross_tenant`, `tests_waha_isolation` e `tests_integration`). Clientes consultam somente seus próprios agendamentos; profissionais ficam limitados à empresa e à própria agenda; gestores não conseguem editar usuários ou serviços de outra empresa; disponibilidade e reservas rejeitam serviços/profissionais de empresas diferentes; bloqueios e fila usam a empresa do usuário; e as notificações WhatsApp usam somente a sessão `tenant_<empresa_id>` correta.

O catálogo público de profissionais e serviços já envia `empresa_id` no fluxo do wizard frontend. Antes da correção abaixo, chamadas anônimas sem esse filtro podiam listar itens ativos globalmente.

Correção aplicada depois da revisão: chamadas anônimas a `/api/usuarios/` e `/api/servicos/` sem `empresa_id` agora retornam `400`; com `empresa_id`, retornam somente profissionais/serviços ativos daquela empresa. Os testes de catálogo público e isolamento foram atualizados. A suíte direcionada executou os cenários de agenda, cross-tenant, integração e segurança; os novos casos de ausência de empresa passaram. Repetir a suíte completa antes de qualquer publicação.

## Próxima retomada — segurança e produção (22/09/2026)

O usuário informou que o backup será provido pela Vultr. Na retomada, confirmar se o backup cobre PostgreSQL e volume de mídia/fotos, sua retenção e realizar um ensaio de restauração antes da publicação.

Estado do código: a branch local `codex/integracao-develop-20260920` contém o commit `62f4338`, que exige `empresa_id` nas listagens públicas de profissionais e serviços. Esse commit ainda não foi enviado para `develop`; a branch local está dois commits à frente do remoto. Há uma foto local não rastreada do banco de prévia, que deve permanecer fora do Git.

Próximos passos combinados:

1. Enviar o commit `62f4338` para `develop` quando autorizado.
2. Confirmar cache compartilhado de produção para o rate limit (Redis/Memcached ou configuração equivalente).
3. Validar migrações, testes e restauração em PostgreSQL de homologação.
4. Revisar a migração de JWT do `localStorage` para mecanismo mais resistente a XSS.
5. Homologar Nginx, WAHA, SMTP e Mercado Pago antes de publicar.

Não publicar em produção nem executar seed até concluir essas verificações.

## Homologação local de Nginx, WAHA, SMTP e Mercado Pago (22/09/2026)

A etapa local foi executada e documentada em `deploy/HOMOLOGACAO_INTEGRACOES.md`. Nenhuma chamada real de pagamento, mensagem ou e-mail foi feita e produção não foi alterada.

- Credenciais WAHA foram removidas do Compose atual e substituídas por variáveis obrigatórias. Como o valor anterior esteve versionado, a rotação continua obrigatória.
- SMTP passou a validar TLS/SSL e campos obrigatórios em produção; destinatários de alerta usam `EMAIL_ALERT_TO`.
- Mercado Pago agora registra cobranças locais, exige administrador, limita os planos, confere valor/moeda e processa webhook de forma idempotente. Foi criada a migração `payments.0001_initial`.
- Sete testes dedicados passaram. Frontend: lint, sete testes e build aprovados. Os oito testes do entrypoint passaram fora do sandbox Windows. Checagens Django e de migrações passaram.
- O daemon Docker local não estava ativo e o Nginx não está instalado localmente; falta `nginx -t` na imagem candidata e o ensaio conectado com credenciais TEST/caixas/números autorizados.

Antes de publicar: aplicar a nova migração em homologação, rotacionar WAHA, validar a cadeia TLS/Nginx, testar SMTP real e executar o fluxo Mercado Pago com credenciais TEST. Manter `PERMITIR_PAGAMENTOS=False` até a conclusão.

## Redesign visual e depoimentos ilustrativos (22/09/2026)

O frontend recebeu uma nova direção visual para substituir o estilo escuro/dourado considerado vintage. A identidade agora usa azul-noite, coral, laranja e ciano, com tipografia mais forte, maior contraste, gradientes contemporâneos e superfícies translúcidas. Os fluxos funcionais de login, cadastro, agendamento e painéis foram preservados.

A landing page foi reorganizada com hero em vídeo, chamada principal objetiva, painel visual de agenda, recursos e nova chamada de conversão. Foi criada uma seção de conversas inspirada no modo escuro do WhatsApp, com fundo texturizado, balões recebidos/enviados, horários e confirmação de leitura.

Os depoimentos de Rafael, Juliana e Marcos são explicitamente identificados na interface como **exemplos ilustrativos**, não como avaliações de clientes reais. Foram gerados três retratos fictícios por IA e incluídos em `frontend/src/imagem/depoimento-*.png`. Não remover a indicação de conteúdo ilustrativo sem substituir os textos e imagens por depoimentos reais autorizados.

Validações depois do redesign: lint aprovado, sete testes Vitest aprovados e build Vite aprovado. O bundle principal continua grande (aproximadamente 1,57 MB) e os três retratos somam aproximadamente 6,4 MB; otimizar carregamento/imagens antes da publicação definitiva. A prévia local foi executada em `127.0.0.1:3000`, com backend local em `127.0.0.1:8000` e conta de demonstração separada de produção.

Estado antes do envio solicitado: alterações de integração, pagamentos e visual ainda estavam no diretório de trabalho. A foto local `backend/media/profissionais/carlos.barbergoldenbarber.com_b1f33bd6.jpg` pertence ao banco de prévia e deve permanecer fora do Git. Logs, SQLite, `.env` e credenciais também não devem ser enviados.

## Como retomar localmente

## Atualização de produção em andamento (23/09/2026)

O usuário autorizou o envio das melhorias para `develop` e iniciou a atualização guiada no servidor Vultr. Não há segredos registrados neste documento.

### Código e migrações

- O commit `93fdc0d` (`perf: adiciona redis e otimiza frontend`) foi enviado para `origin/develop`.
- O servidor estava em `ca9b786`, oito commits atrás, e continha duas migrações não rastreadas já registradas como aplicadas no PostgreSQL: `tenants.0008_empresa_horas_limite_cancelamento` e `tenants.0009_merge_20260721_0129`.
- As duas migrações originais do servidor foram movidas, sem exclusão, para `/root/SaaS_barbearia_pro_migration_backup_20260923/`.
- Foi criada uma migração de compatibilidade vazia para `0008_empresa_horas_limite_cancelamento`, porque o campo já está consolidado em `0007`, e preservado o merge `0009`. Uma migração completa em SQLite novo passou. Commit `d161bb5` enviado para `develop`.
- O servidor executou `git pull --ff-only origin develop` de `ca9b786` até `d161bb5`. Permaneceram não rastreados e preservados: a foto `backend/media/profissionais/pedro_0SJUBdN.jpg`, `backend/staticfiles/` e `backend/test_error.py`.
- O plano do PostgreSQL mostrou somente `payments.0001_initial` pendente, que cria `CobrancaAssinatura`. Essa migração **ainda não foi aplicada**.
- A auditoria encontrou um único agendamento legado concluído: empresa e serviços corretos, mas o mesmo perfil administrador havia sido usado historicamente como cliente e profissional. Nenhum dado foi alterado. A auditoria foi ajustada para tolerar perfil legado somente em registros finais (`CONCLUIDO`/`CANCELADO`), mantendo os bloqueios de empresa/serviço e de agendamentos ativos. Dois testes passaram. Commit `ef48955` enviado para `develop`.
- **Ponto atual:** o servidor ainda precisa executar `git pull --ff-only origin develop` para receber `ef48955` e repetir `docker compose run --rm --no-deps backend python manage.py auditar_agenda --fail-on-issues`. Não aplicar migrações antes dessa confirmação.

### Redis e rate limit

- O Compose candidato foi validado com `docker compose config --quiet`.
- As imagens candidatas de backend e frontend foram construídas com sucesso no servidor.
- O Redis 7.4 Alpine foi iniciado isoladamente com `docker compose up -d redis`; não há porta publicada. `redis-cli ping` retornou `PONG`.
- O Django candidato gravou e leu no cache compartilhado; resultado `CACHE_OK=True`.
- O backend/frontend atuais ainda não foram recriados, portanto o rate limit da aplicação em execução ainda não usa o novo Redis.

### Nginx e frontend

- `docker compose run --rm --no-deps frontend nginx -t` passou: sintaxe e configuração válidas.
- O aviso de container órfão `barbeiro_pro_db` é esperado porque o PostgreSQL ativo continua ausente do Compose atual. Não executar `--remove-orphans`, `docker compose down` ou limpeza de volumes.
- A imagem frontend otimizada foi construída, mas o container frontend em produção ainda não foi substituído.

### Credenciais e variáveis

- A chave da API e a senha administrativa do WAHA foram rotacionadas diretamente no servidor sem impressão dos valores. A nova `WAHA_API_KEY` está sincronizada em `.env` e `backend/.env`; `WAHA_ADMIN_USER` e `WAHA_ADMIN_PASSWORD` estão no `.env` do Compose.
- Cópias protegidas anteriores à rotação estão em `/root/SaaS_barbearia_pro_env_backup_20260923/`, com nomes distintos para Compose e backend. Não copiar esses arquivos para o Git nem compartilhar seu conteúdo.
- A nova credencial WAHA ainda não está ativa porque os containers WAHA/backend não foram recriados. Preservar o volume `waha_data` durante a troca.
- A chave Django antiga não atendia ao mínimo de segurança e foi rotacionada no servidor. `DJANGO_SECRET_KEY`, domínios permitidos, CORS, CSRF, proxy HTTPS e PostgreSQL foram configurados. A rotação invalidará sessões/JWT atuais quando o backend novo iniciar; usuários precisarão entrar novamente.
- `python manage.py check --deploy` passou com somente dois avisos opcionais: HSTS para subdomínios e preload. Não ativar essas opções sem confirmar que todos os subdomínios usam HTTPS.
- `PERMITIR_PAGAMENTOS=False` está explícito no Compose e no `backend/.env`. O Mercado Pago existente foi preservado; nenhuma transação real foi executada nesta etapa.

### SMTP

- Host, usuário, senha e remetente SMTP já existiam no servidor. `EMAIL_ALERT_TO` foi configurado internamente com a conta SMTP existente, sem exibir o endereço.
- O envio conectado retornou `SMTP_ENVIADOS=1`, confirmando aceitação pelo servidor SMTP. A confirmação visual de chegada na caixa de entrada/spam ainda não foi informada pelo usuário.

### Próxima sequência segura

1. No servidor, receber `ef48955` com `git pull --ff-only origin develop`.
2. Repetir `auditar_agenda --fail-on-issues`; o resultado esperado é zero inconsistências.
3. Confirmar visualmente a chegada do e-mail SMTP.
4. Aplicar somente `payments.0001_initial` de forma controlada.
5. Recriar coordenadamente WAHA, backend e frontend, sem `down`, sem `--remove-orphans` e sem remover volumes. A troca ativa Redis, nova chave Django e credenciais WAHA; pode ser necessário reconectar a sessão WhatsApp por QR code.
6. Verificar containers, logs filtrados, HTTP/HTTPS, login, catálogo público, painel e status WAHA. Enviar mensagem apenas para número autorizado.
7. Manter pagamentos desabilitados até a homologação final. A confirmação do backup Vultr continua por último, conforme solicitado pelo usuário, mas permanece obrigatória antes da publicação definitiva.

### Ordem ajustada pelo usuário (23/09/2026)

A confirmação de que o backup da Vultr cobre o PostgreSQL e o volume de fotos/mídia deve ficar por último no plano de preparação. Antes disso, continuar as verificações locais e a homologação que não alteram produção. A publicação em produção continua condicionada à confirmação do backup e dos demais requisitos de segurança.

## Cache, integrações e otimização (23/09/2026)

- O candidato de produção passou a usar Redis compartilhado para o rate limit (`redis://redis:6379/1`). O Compose inclui Redis 7.4 Alpine sem porta publicada, com healthcheck, limite de 128 MB e política LRU; o backend aguarda o serviço saudável.
- `PERMITIR_PAGAMENTOS=False` ficou explícito no Compose. O usuário confirmou que o Mercado Pago já funciona em produção; não executar transações reais durante os demais testes.
- A mesma `WAHA_API_KEY` do ambiente do Compose agora é injetada no backend e no WAHA, evitando divergência durante a rotação. A chave e as senhas reais continuam fora do Git. A rotação no servidor ainda depende de acesso ao terminal e deve preservar `waha_data`.
- Os três retratos foram convertidos de PNG 1254x1254 (aproximadamente 6,4 MB) para WebP 512x512 (aproximadamente 74 KB no total), com inspeção visual aprovada.
- Telas administrativas, agenda, assinatura e financeiro passaram a carregar sob demanda. PDF, html2canvas e o painel financeiro foram separados em chunks próprios. O maior arquivo inicial caiu de aproximadamente 1,57 MB para aproximadamente 400 KB; nenhum chunk final excede 500 KB.
- Validações: 26 testes direcionados do backend aprovados, incluindo Redis, bloqueio de pagamentos, segurança, WAHA/SMTP simulados e Mercado Pago; frontend com lint, 7 testes e build aprovados; `pip check`, `manage.py check`, `git diff --check` e `docker compose config --quiet` aprovados.
- Docker local permanece sem daemon, portanto `nginx -t`, Redis em execução e ensaios conectados de SMTP/WAHA precisam ser feitos na imagem/servidor de homologação. Nenhuma credencial real foi solicitada ou registrada.

Não reinstalar nem refazer alterações sem necessidade. Leia este arquivo e os dois guias, confira `git status` e prossiga do próximo passo pendente.

Para repetir testes backend quando houver novas alterações, a partir de `backend`, no PowerShell:

```powershell
$env:DJANGO_DEBUG = 'True'
$env:TEST_DATABASE_NAME = Join-Path $PWD 'test-concurrency.sqlite3'
..\.venv\Scripts\python.exe manage.py test --noinput
```

O arquivo indicado por TEST_DATABASE_NAME é descartável: o Django o cria e destrói. Nunca utilizar caminho ou credenciais de produção nos testes.

No frontend: `npm.cmd run lint`, `npm.cmd test` e `npm.cmd run build`. O ambiente restrito bloqueou esbuild e downloads em algumas execuções; quando isso ocorreu, foi necessário solicitar a execução com a permissão apropriada. Não confundir bloqueio do ambiente com falha do projeto.

## Continuidade após a atualização de produção (24/09/2026)

Esta seção substitui os pontos desatualizados da seção "Atualização de produção em andamento". Não há credenciais, chaves PIX, tokens ou dados pessoais registrados aqui.

### Atualização e verificações concluídas no servidor

- O servidor recebeu as atualizações de `develop`, as imagens de backend e frontend foram construídas e os containers de aplicação foram recriados sem interromper ou remover o PostgreSQL órfão do Compose.
- A auditoria da agenda foi repetida depois do commit `ef48955` e retornou zero inconsistências.
- A migração `payments.0001_initial` foi aplicada com sucesso. `python manage.py migrate --plan` passou a informar que não há operações pendentes.
- O backend iniciou normalmente com Gunicorn, executou as migrações sem pendências e coletou os arquivos estáticos.
- Redis respondeu `PONG` e o teste pelo cache Django retornou `CACHE_OK=True`; o rate limit passou a usar o cache compartilhado.
- O Nginx da imagem frontend passou em `nginx -t`. Pela URL pública HTTPS, a página inicial respondeu 200, a API protegida respondeu 401 e o Django Admin respondeu 200.
- Requisições diretas ao IP produziram `DisallowedHost`, comportamento esperado. Não adicionar o IP público aos hosts permitidos apenas para eliminar sondagens diretas.
- O teste SMTP conectado foi aceito pelo servidor (`SMTP_ENVIADOS=1`). Ainda registrar separadamente se a mensagem chegou na caixa de entrada ou spam.
- O WAHA respondeu HTTP 200 com a chave rotacionada. A sessão foi reconectada pelo QR code e a interface da aplicação indicou conexão bem-sucedida. O volume persistente `saas_barbearia_pro_waha_data` está montado em `/app/.waha`.
- A chave secreta Django e as credenciais WAHA foram rotacionadas no servidor sem imprimir os valores. Os backups protegidos de ambiente permanecem fora do repositório.
- Não usar `docker compose down`, `--remove-orphans` ou remover volumes. O container `barbeiro_pro_db` continua sendo um órfão intencional que deve ser preservado.

### Correções funcionais publicadas em `develop`

- `7d42461`: corrigiu o cadastro de serviços por gestores. O serializer agora associa a empresa autenticada sem exigir que o frontend envie o tenant e preserva a validação de nomes duplicados por empresa.
- `f712990`: novos membros cadastrados em Gestão de Equipe passam a ser profissionais por padrão. Uma conta criada anteriormente com tipo incorreto foi corrigida de forma controlada no servidor.
- `9dfc40d`: o painel do cliente agora mostra o motivo devolvido pela API quando um cancelamento é bloqueado. No caso verificado, faltavam aproximadamente 10 a 11 horas para o atendimento e a empresa exigia 24 horas de antecedência; a regra estava correta e somente a mensagem era genérica.
- `8ce75dd`: a mensagem de solicitação do sinal PIX foi suavizada. Ela explica que o horário foi reservado especialmente para o cliente, que os 50% confirmam a reserva, mantém o prazo de 15 minutos e usa o limite de cancelamento configurado na empresa em vez de texto fixo de 24 horas.
- Para a empresa nova verificada, `exigir_sinal` foi ativado de forma controlada. Naquele momento a chave PIX e o beneficiário ainda não estavam configurados; o usuário informou que faria essa configuração pela interface. Nunca registrar ou compartilhar a chave neste arquivo.
- `6e4dfff`: o Django Admin recebeu as ações "Desativar clientes selecionados (preserva o histórico)" e "Reativar clientes selecionados". A remoção definitiva continua bloqueada porque as relações usam exclusão em cascata e apagariam histórico de agenda/fidelidade.
- `91284c6`: o Django Admin recebeu um filtro combinado com "Clientes ativos" e "Clientes inativos". Essa versão foi construída e o backend foi recriado com sucesso no servidor.
- `c023205`: o Compose deixou de sobrescrever `PERMITIR_PAGAMENTOS` com `False`; a chave volta a ser controlada por `backend/.env`. O padrão documentado permanece `False`. Sempre conferir o valor efetivamente carregado no container depois de qualquer alteração e recriar somente o backend.
- `463278d`: o backend passou a aceitar assinatura por 2 meses, alinhando-se às opções que o frontend já exibia. O valor esperado é calculado como `2 x R$ 49,99 = R$ 99,98`, e foi adicionado teste de regressão. Este commit foi enviado para `develop`, mas ainda falta confirmação explícita de que foi puxado, construído e recriado no servidor.

### Acesso administrativo ao WAHA

- O painel WAHA não está publicado na internet; o serviço usa somente `expose: 3000` na rede Docker.
- O acesso deve ser feito por túnel SSH local. O IP interno observado foi `172.18.0.3`, mas ele pode mudar depois de recriar o container; sempre consultar novamente com `docker inspect` antes de abrir o túnel.
- Com o túnel ativo, o painel é acessado em `http://127.0.0.1:3001/dashboard`. Usuário e senha estão em `WAHA_ADMIN_USER` e `WAHA_ADMIN_PASSWORD` no `.env` da raiz do projeto no servidor. Não publicar a porta, não copiar esses valores para o Git e não registrar as credenciais neste documento.
- Para abrir o arquivo correto no servidor, primeiro entrar em `/root/SaaS_barbearia_pro` e usar `nano .env`. O erro "Directory 'backend' does not exist" ocorreu porque o comando havia sido executado a partir de `/root`.

### Estado e próximos passos

1. Confirmar se o servidor recebeu o commit `463278d`; se não, executar pull, construir e recriar somente o backend. Depois testar a opção de assinatura por 2 meses.
2. Verificar no container o valor atual de `PERMITIR_PAGAMENTOS`. Não presumir que continua `False`, pois o usuário iniciou testes reais da tela de pagamento. Alterações em `backend/.env` só entram no processo após recriar o backend.
3. Testar um novo agendamento com sinal depois de configurar PIX/beneficiário, usando apenas dados e número autorizados, e confirmar o texto acolhedor enviado pelo WhatsApp.
4. Confirmar visualmente o recebimento do teste SMTP, caso ainda não tenha sido feito.
5. Continuar preservando os arquivos não rastreados do servidor e a foto local de prévia. A foto local `backend/media/profissionais/carlos.barbergoldenbarber.com_b1f33bd6.jpg` permanece fora do Git.
6. Por solicitação do usuário, deixar por último a confirmação de que o backup Vultr cobre PostgreSQL e fotos/mídia. Apesar de ficar por último na ordem operacional, essa confirmação é um requisito antes de considerar a publicação definitivamente homologada.

## Auditoria de portas e endurecimento de rede (24/09/2026)

Foi feita uma verificação das portas realmente abertas no host e um teste externo a partir de outra rede. Nenhum segredo foi registrado.

### Exposição encontrada e correções

- Nginx público permanece nas portas `80` e `443`, como necessário para o site.
- SSH permanece público na porta `22`. Revisar posteriormente autenticação por chave, bloqueio de login root por senha e restrição por IP, sem alterar acesso antes de preparar uma sessão de recuperação.
- O backend já estava vinculado somente a `127.0.0.1:8000`. Teste externo confirmou `TcpTestSucceeded=False`.
- Redis e WAHA não aparecem como portas publicadas no host; permanecem na rede Docker.
- O PostgreSQL órfão estava publicado em todas as interfaces na porta `5432`. Teste externo confirmou que a porta respondia pela internet.
- Foram adicionadas regras IPv4 e IPv6 na cadeia `DOCKER-USER`, limitadas à interface pública, para descartar conexões externas destinadas à porta `5432`. Depois da mudança, o teste externo retornou `False`, enquanto o backend confirmou `DATABASE_OK=True` pela rede interna.
- O frontend Docker estava publicado em todas as interfaces na porta `3000`. Regras temporárias foram adicionadas ao firewall e o Compose foi corrigido no commit `70ad17e` para usar `127.0.0.1:3000:80`. O container frontend foi recriado e `docker compose ps frontend` confirmou somente o vínculo local. Teste externo retornou `TcpTestSucceeded=False`.
- O aviso do container órfão `barbeiro_pro_db` continua esperado. Não usar `--remove-orphans`, `docker compose down` ou remover volumes.

### Persistência do firewall

- Foi instalado `iptables-persistent`/`netfilter-persistent` e as regras IPv4/IPv6 foram salvas em `/etc/iptables/rules.v4` e `/etc/iptables/rules.v6`. Os dois arquivos contêm o bloqueio externo da porta `5432` na cadeia `DOCKER-USER`.
- Atenção: nessa versão do Ubuntu, a instalação de `iptables-persistent` removeu o pacote `ufw` por conflito. As cadeias e regras que o UFW já havia carregado permaneceram na memória e foram incluídas no estado salvo, mas o comando `ufw` não deve mais ser tratado como a fonte de verdade.
- Não reiniciar o servidor apenas para testar essas regras. Quando houver janela segura e backup confirmado, validar cuidadosamente a restauração do `netfilter-persistent` após reboot, mantendo uma sessão/console de recuperação disponível para não perder o acesso SSH.
- Depois de qualquer mudança no firewall, repetir testes externos das portas `22`, `80`, `443`, `3000`, `5432` e `8000`, além de confirmar o acesso interno do backend ao banco.

### Nginx do host

- Após restringir o frontend ao loopback, o site apresentou `502` porque o Nginx do host ainda encaminhava a rota principal para o IP público na porta `3000`.
- A configuração ativa `/etc/nginx/sites-available/salaopro.site` foi ajustada para encaminhar o frontend a `127.0.0.1:3000` e o backend a `127.0.0.1:8000`.
- Antes das alterações foram criadas cópias locais no servidor com os sufixos `.before-loopback-20260924` e `.before-backend-loopback-20260924`. Não enviar esses arquivos ao Git e não removê-los por enquanto.
- `nginx -t` passou antes de cada reload. Após a correção, os testes públicos retornaram `frontend=200`, `api=401` e `admin=200`. O `401` na raiz protegida da API é esperado e confirma exigência de autenticação.

### Superfície pública intencional

- A aplicação expõe `/api/` por HTTPS porque frontend, cadastro e agendamento público dependem dela.
- Permanecem públicas somente as operações necessárias, como login/refresh, cadastro, catálogo público filtrado por empresa, disponibilidade, entrada na fila e webhook do Mercado Pago. Rotas de agenda privada, financeiro, criação de cobrança e controle do WAHA exigem autenticação/permissões.
- Arquivos de mídia em `/arquivos/` também são públicos. Revisar futuramente se o volume contém somente fotos destinadas à exibição pública.

### Retomada após esta auditoria

1. Confirmar o valor efetivamente carregado de `PERMITIR_PAGAMENTOS` e testar a assinatura de 2 meses; o código `463278d` já está presente no checkout do servidor, mas ainda falta confirmação funcional final.
2. Registrar no repositório uma referência segura da configuração Nginx do host, sem certificados, chaves ou dados específicos do servidor, para evitar divergência futura.
3. Revisar a política SSH e a persistência do firewall em janela controlada.
4. Manter por último, conforme solicitado, a confirmação de que o backup Vultr cobre PostgreSQL e fotos/mídia, seguida de ensaio de restauração antes de considerar a homologação encerrada.

## Confirmações operacionais do usuário (24/09/2026)

Esta seção registra o estado final e substitui as pendências históricas conflitantes das seções anteriores.

- O usuário confirmou que controla `PERMITIR_PAGAMENTOS` pelo arquivo de ambiente no servidor e que o fluxo de pagamentos está funcionando.
- Um novo agendamento com sinal PIX e envio por WhatsApp foi testado com dados autorizados e funcionou.
- A entrega SMTP foi confirmada visualmente na caixa de entrada por meio de um alerta do monitoramento do WAHA. O alerta exibido era referente a uma desconexão anterior; o usuário confirmou que o WhatsApp está conectado e enviando normalmente depois da reconexão.
- Inicialmente o usuário acreditava que o backup da Vultr estava ativo, mas o painel confirmou `Auto Backups: Not Enabled`. Foi adotado e validado um backup manual de PostgreSQL e mídia; o backup automático pago continua desativado.
- Os pontos antes pendentes desta etapa foram concluídos: assinatura de 2 meses, referência sanitizada do Nginx, endurecimento do SSH, persistência do firewall após reboot e ensaio isolado de restauração do backup manual.
- O teste isolado `MercadoPagoHomologationTests.test_admin_can_pay_for_two_months` passou no container de produção com redirecionamento HTTPS desativado somente para o processo de teste. O Mercado Pago foi simulado, nenhuma cobrança real foi criada, e foram validados 2 meses por R$ 99,98.
- A configuração observada do Nginx do host foi registrada sem certificados ou parâmetros secretos em `deploy/references/host.nginx.production.sanitized.conf`. Ela ainda contém rotas legadas `/admin/`, `/static/` e `/media/`; o Nginx interno do frontend usa `/painel-master/`, `/estaticos/` e `/arquivos/`. Como o acesso público está funcional, essa divergência foi apenas documentada e não foi alterada no servidor.
- O acesso SSH foi endurecido depois da criação e validação de uma nova chave Ed25519 protegida por frase secreta. O arquivo `/etc/ssh/sshd_config.d/00-salaopro-hardening.conf` define autenticação por chave, `PermitRootLogin prohibit-password`, desativa senha, autenticação interativa e X11 forwarding. `sshd -t` passou, o serviço permaneceu ativo após reload, uma nova conexão por chave retornou `ACESSO_SEGURO_OK` e uma tentativa forçada por senha foi recusada com `Permission denied (publickey)`. A sessão existente foi mantida durante a validação. Há uma cópia de segurança em `/etc/ssh/sshd_config.before-key-hardening-20260924`.
- A chave SSH antiga, cuja frase secreta não estava mais disponível, foi removida de `authorized_keys` depois de criar a cópia `/root/.ssh/authorized_keys.before-old-key-removal-20260924`. Somente a chave nova identificada pelo comentário `salaopro-vultr` permanece autorizada; uma conexão independente por ela retornou `CHAVE_UNICA_OK`.
- Como alternativa ao backup automático da Vultr, que acrescentaria 20% ao preço-base da instância, foi criado um backup manual consistente em `/root/salaopro-backup-20260924`: dump PostgreSQL em formato customizado e arquivo compactado do volume de mídia. Os arquivos foram validados, baixados para `C:\Users\lucia\Desktop\salaopro-backup-20260924` e os hashes SHA-256 locais coincidiram com os do servidor. O dump foi restaurado com sucesso em um PostgreSQL 15 Alpine temporário e isolado, resultando em 20 tabelas e 55 migrações; o container temporário foi removido. O backup automático da Vultr permanece desativado.
- Depois do backup e da validação das políticas de reinício dos containers, o servidor foi reiniciado de forma autorizada. Após o reboot, `netfilter-persistent` restaurou os bloqueios IPv4 e IPv6 da porta 5432 (`FIREWALL_POS_REBOOT_OK`). Frontend, backend, WAHA, Redis e PostgreSQL retornaram; Redis ficou saudável, o backend confirmou `DATABASE_OK=True`, e os testes públicos retornaram frontend 200, API 401 e painel 200.
- A sessão WAHA `tenant_3` permaneceu em estado `WORKING` após a reinicialização, com resposta HTTP 200 da API interna.

## Procedimento de backup manual e restauração (24/09/2026)

O backup manual protege os dados principais da aplicação sem o custo adicional do backup automático da Vultr. Ele não é uma imagem completa do servidor. Repetir periodicamente, baixar os arquivos para outro equipamento e conferir os hashes. Não enviar por e-mail porque os arquivos contêm dados da aplicação e anexos podem falhar ou exceder limites.

### Criar e validar o backup no servidor

```bash
SALAOPRO_BACKUP_TAG=$(date +%Y%m%d-%H%M%S)
SALAOPRO_BACKUP_DIR="/root/salaopro-backup-$SALAOPRO_BACKUP_TAG"
install -d -m 700 "$SALAOPRO_BACKUP_DIR"
docker exec barbeiro_pro_db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$SALAOPRO_BACKUP_DIR/postgresql.dump"
tar -C /var/lib/docker/volumes/saas_barbearia_pro_django_media/_data -czf "$SALAOPRO_BACKUP_DIR/media.tar.gz" .
docker exec -i barbeiro_pro_db pg_restore -l < "$SALAOPRO_BACKUP_DIR/postgresql.dump" > /dev/null
tar -tzf "$SALAOPRO_BACKUP_DIR/media.tar.gz" > /dev/null
sha256sum "$SALAOPRO_BACKUP_DIR/postgresql.dump" "$SALAOPRO_BACKUP_DIR/media.tar.gz"
echo "$SALAOPRO_BACKUP_DIR"
```

No PowerShell local, substituir o sufixo pela pasta exibida e baixar com a chave nova:

```powershell
scp -i "$env:USERPROFILE\.ssh\id_ed25519_salaopro" -o IdentitiesOnly=yes -r root@140.82.30.186:/root/salaopro-backup-AAAAMMDD-HHMMSS "$env:USERPROFILE\Desktop\"
Get-FileHash "$env:USERPROFILE\Desktop\salaopro-backup-AAAAMMDD-HHMMSS\postgresql.dump","$env:USERPROFILE\Desktop\salaopro-backup-AAAAMMDD-HHMMSS\media.tar.gz" -Algorithm SHA256
```

Os hashes locais devem ser idênticos aos hashes calculados no servidor.

### Ensaio de restauração isolado

O teste abaixo não publica porta e não toca no PostgreSQL de produção:

```bash
SALAOPRO_RESTORE_DIR="/root/salaopro-backup-AAAAMMDD-HHMMSS"
docker run -d --rm --name salaopro_restore_test -e POSTGRES_PASSWORD=restore-test-only postgres:15-alpine
until docker exec salaopro_restore_test pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done
docker exec salaopro_restore_test createdb -U postgres restore_test
docker exec -i salaopro_restore_test pg_restore -U postgres -d restore_test --no-owner --no-privileges --exit-on-error < "$SALAOPRO_RESTORE_DIR/postgresql.dump"
docker exec salaopro_restore_test psql -U postgres -d restore_test -Atc "SELECT 'TABELAS=' || count(*) FROM pg_tables WHERE schemaname='public'; SELECT 'MIGRACOES=' || count(*) FROM django_migrations;"
docker stop salaopro_restore_test
```

### Restauração real em produção

Esta operação substitui o banco atual e causa indisponibilidade. Antes dela, manter um backup adicional do estado atual. Não executar `docker compose down`, `--remove-orphans` nem remover volumes.

```bash
cd /root/SaaS_barbearia_pro
SALAOPRO_RESTORE_DIR="/root/salaopro-backup-AAAAMMDD-HHMMSS"
docker compose stop backend frontend
docker exec barbeiro_pro_db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "/root/pre-restore-$(date +%Y%m%d-%H%M%S).dump"
docker exec barbeiro_pro_db sh -c 'dropdb --force -U "$POSTGRES_USER" "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" -O "$POSTGRES_USER" "$POSTGRES_DB"'
docker exec -i barbeiro_pro_db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges --exit-on-error' < "$SALAOPRO_RESTORE_DIR/postgresql.dump"
tar -C /var/lib/docker/volumes/saas_barbearia_pro_django_media/_data -czf "/root/media-before-restore-$(date +%Y%m%d-%H%M%S).tar.gz" .
tar -C /var/lib/docker/volumes/saas_barbearia_pro_django_media/_data -xzf "$SALAOPRO_RESTORE_DIR/media.tar.gz"
docker compose up -d backend frontend
docker compose exec -T backend python manage.py migrate --plan
docker compose exec -T backend python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('DATABASE_OK=True')"
docker compose ps
```

Depois da restauração, validar HTTPS: página inicial 200, `/api/` 401, `/painel-master/login/` 200, Redis saudável e sessão WAHA em `WORKING`.

## Senhas, Termos de Uso e privacidade (24/09/2026)

- Os cadastros públicos de barbearia e cliente agora exibem requisitos de senha com indicadores individuais, confirmação da senha e bloqueio do envio enquanto houver requisito pendente.
- A criação e alteração de senha de membros da equipe também exibe os mesmos indicadores. O backend passou a exigir, além dos validadores nativos do Django, letra maiúscula, letra minúscula, número e caractere especial.
- O cadastro público exige checkbox de concordância com os Termos de Uso e ciência do Aviso de Privacidade. O backend rejeita cadastros sem aceite e registra o aceite, data/hora e IP de origem nos campos já existentes do usuário.
- Foi criado um modal de Termos de Uso e Aviso de Privacidade, acessível nos cadastros e no rodapé público. O texto cobre serviço, responsabilidades, categorias e finalidades de dados, bases legais, papéis de controlador/operador, compartilhamentos, retenção, segurança, direitos do titular, comunicações, encerramento e contato. A versão operacional deve receber revisão jurídica antes de ser considerada parecer de conformidade.
- A implementação foi baseada nos princípios e direitos da Lei nº 13.709/2018 e em materiais orientativos da ANPD. Ela não presume que todo tratamento dependa de consentimento.
- Validações locais: lint aprovado; 9 testes frontend aprovados; build Vite aprovado; 36 testes direcionados do backend aprovados; `git diff --check` aprovado.

### Publicação em produção (25/09/2026)

- Funcionalidade enviada à `develop` no commit `120e809`; o fixture PostgreSQL do teste foi corrigido no commit `8d7a9ae`, usando CNPJ sem pontuação para respeitar o limite de 14 caracteres.
- Antes da atualização foi criado e validado o backup `/root/salaopro-predeploy-20260925-015559`, contendo dump PostgreSQL e mídia compactada. O dump e o arquivo de mídia passaram nas verificações estruturais e receberam hashes SHA-256.
- O servidor avançou por `git pull --ff-only` até `8d7a9ae`. Os arquivos não rastreados `backend/media/profissionais/pedro_0SJUBdN.jpg` e `backend/test_error.py` foram preservados.
- Imagens de backend e frontend construídas com sucesso. O teste de registro de aceite passou no PostgreSQL candidato e `nginx -t` passou no frontend candidato.
- Somente backend e frontend foram recriados com `docker compose up -d --no-deps backend frontend`. Não houve `down`, remoção de órfãos ou remoção de volumes. O PostgreSQL órfão foi preservado.
- Inicialização: configuração Django válida, nenhuma migração pendente, arquivos estáticos coletados, Gunicorn e Nginx ativos.
- Verificação final: frontend 200, API protegida 401, painel 200, `DATABASE_OK=True`, Redis `PONG` e sessão WAHA `tenant_3` em `WORKING` com HTTP 200.

## Marketing, testes ponta a ponta e homologação complementar (25/09/2026)

### Materiais de marketing locais

- Foi criada a pasta `marketing/` com artes e vídeos promocionais. As versões mais importantes são `marketing/salaopro-video-30s-prints-reais.mp4`, montada somente com os prints reais enviados pelo usuário, e `marketing/checklist-funcoes-gestor-salaopro.png`, com as funções disponíveis ao gestor.
- Os prints originais foram guardados em `marketing/prints-reais/`. Os scripts `marketing/render_video_real.py` e `marketing/criar_checklist_gestor.py` permitem reproduzir os materiais. O primeiro vídeo e as imagens geradas artificialmente permanecem como versões anteriores; para divulgação do funcionamento real, preferir a versão `prints-reais`.
- Foi instalada localmente, fora do código da aplicação, a dependência `imageio-ffmpeg` em `.video_tools/` para codificação dos vídeos. Não é uma dependência de produção.

### Jornada completa automatizada em ambiente local

- Foi criado `backend/apps/agenda/tests_e2e_journey.py`, que testa por API a jornada completa em banco descartável: cadastro da barbearia e gestor, período de teste, configurações, criação de serviço e profissional, catálogo público sem dados privados, cadastro do cliente com aceite dos termos, disponibilidade, agendamento, ocupação do horário, visualização pelo gestor, confirmação e visualização pelo cliente.
- A jornada passou isoladamente. Em conjunto com `apps.agenda.tests_integration`, foram executados **11 testes aprovados**.
- O teste observou que `registrar_saas` calcula `data_fim_trial` com `timezone.now().date()` (UTC). Perto da virada do dia em São Paulo isso pode conceder um dia adicional. O usuário decidiu manter o comportamento e tratá-lo como bônus; não corrigir sem nova solicitação.
- O teste existente `BusinessRulesTests.test_cancel_frees_slot` foi reforçado: antes do cancelamento, o horário deve estar em `horarios_ocupados`; depois, deve voltar para `horarios_disponiveis`, sair dos ocupados e o registro deve permanecer com status `CANCELADO`. O teste isolado passou. Uma segunda tentativa de cancelamento é recusada, como esperado.

### Jornada controlada executada em produção

- Com autorização explícita do usuário, `backend/qa_production_journey.py` executou uma homologação real pela API pública HTTPS sem imprimir tokens, senhas ou telefone.
- A empresa de homologação `QA Homologação ...`, ID `4`, foi criada. Foram validados cadastro do gestor, serviço, profissional, cliente, consulta de disponibilidade, criação do agendamento, confirmação pelo gestor, visualização pelo cliente, cancelamento e liberação imediata do horário.
- Ao terminar, serviço e profissional de teste foram desativados e a empresa ID `4` foi desativada. Uma consulta pública posterior confirmou que ela não aparece no catálogo ativo. Preservar o histórico para auditoria.
- Como cada empresa possui sessão WAHA própria e a empresa de homologação não tinha WhatsApp conectado, a entrega real foi testada separadamente na empresa ativa ID `3`, que já possuía WAHA conectado. Foi criado o agendamento de teste ID `17` para **02/10/2026 às 09:00**, usando o número autorizado pelo usuário; o agendamento foi cancelado logo depois e o horário voltou a ficar disponível.
- O sistema disparou as mensagens de criação e cancelamento para o cliente. A confirmação visual do recebimento pelo usuário ainda deve ser registrada se ele responder. O agendamento ID `17` e o cliente QA permanecem no histórico real; o agendamento está cancelado e não ocupa a agenda.
- O script de QA de produção é potencialmente mutável: não executá-lo novamente por rotina nem em CI. Ele requer `QA_CLIENT_PHONE` e cria registros reais.

### Fluxo financeiro conferido em produção

- O usuário perguntou por que um atendimento pago de R$ 80 não aparecia no Dashboard Financeiro. A regra foi conferida: o endpoint financeiro contabiliza apenas agendamentos com status `CONCLUIDO`, não apenas `PAGO` ou `CONFIRMADO`.
- O usuário alterou o atendimento para `CONCLUIDO` e confirmou que faturamento bruto, comissão e lucro líquido apareceram corretamente. O fluxo financeiro de produção está validado nesse ponto.
- Há uma inconsistência visual pendente: `AgendaTable.jsx` calcula “Total de Vendas Hoje” somando `valor_total` de todos os agendamentos exibidos, inclusive confirmados e cancelados, enquanto o Dashboard Financeiro soma somente concluídos. Corrigir o cálculo ou renomear o indicador em uma próxima alteração; nenhuma correção foi aplicada nesta sessão.

### Estado local ao encerrar

- Alterados/novos desta sessão: `backend/apps/agenda/tests.py`, `backend/apps/agenda/tests_e2e_journey.py`, `backend/qa_production_journey.py` e `marketing/`.
- A foto local não rastreada `backend/media/profissionais/carlos.barbergoldenbarber.com_b1f33bd6.jpg` já existia e continua preservada; não adicionar nem remover sem decisão explícita.
- As mudanças desta sessão ainda não receberam commit nem foram enviadas para `develop`. Não descartar os arquivos locais.

## Correção do falso erro após agendamento (27/09/2026)

- Um teste real mostrou a mensagem genérica de falha mesmo com o agendamento criado. O log confirmou `POST /api/agendamentos/` com HTTP 201 e criação do agendamento ID 18, enquanto dois envios WAHA sequenciais atingiram timeout de 10 segundos cada. O Axios do frontend expira em 15 segundos e, por isso, interpretava a resposta demorada como falha.
- O commit `da90c4c` colocou e-mail/WhatsApp em uma fila interna assíncrona quando `AGENDA_NOTIFICATIONS_ASYNC=True` (padrão com `DEBUG=False`). Desenvolvimento e testes com `DEBUG=True` permanecem síncronos por padrão para evitar concorrência com SQLite. A resposta HTTP não aguarda mais o WAHA.
- O frontend passou a exibir mensagens de validação associadas a campos e, em eventual timeout, orienta a conferir “Minha Agenda” antes de tentar novamente.
- Validação local: 78 testes backend aprovados (um ignorado), 11 testes frontend aprovados, lint e build aprovados. Nas imagens candidatas do servidor, os dois testes específicos da fila passaram e `nginx -t` foi aprovado.
- Backup pré-publicação validado em `/root/salaopro-predeploy-20260928-002638`, com dump PostgreSQL e mídia. Somente backend e frontend foram recriados com `docker compose up -d --no-deps backend frontend`; volumes, PostgreSQL, Redis e WAHA foram preservados.
- Pós-publicação: nenhuma migração pendente, Gunicorn 26.2.0 ativo, `DATABASE_OK=True`, Redis `PONG`, frontend 200, API protegida 401 e painel 200. `AGENDA_NOTIFICATIONS_ASYNC=True` e o novo bundle frontend foram confirmados nos containers.
- WAHA: `tenant_3` permaneceu `WORKING`; `tenant_5` estava em `SCAN_QR_CODE`. O comando genérico `check_waha_status` consultou a configuração legada `default`, inexistente, e enviou um alerta por e-mail. Esse alerta isolado não representa queda da sessão principal; revisar futuramente o valor de `WAHA_SESSION` ou tornar o monitoramento multiempresa.
- Permaneceram preservados no servidor os arquivos não rastreados `backend/media/profissionais/pedro_0SJUBdN.jpg` e `backend/test_error.py`. Localmente, a foto e os materiais de marketing não foram incluídos no commit da correção.

## Recuperação de senha por e-mail (27/09/2026)

- Implementada e publicada no commit `802e196`. O login agora oferece “Esqueci minha senha”; a solicitação envia um link por SMTP e a rota pública `/redefinir-senha` permite definir e confirmar uma nova senha.
- O link usa o gerador de tokens do Django, expira em 30 minutos, é de uso único e aplica os mesmos validadores fortes do cadastro. A resposta de solicitação é neutra para não revelar se uma conta existe, e os endpoints reutilizam os limites de autenticação por IP/conta.
- Após a troca, refresh tokens existentes são incluídos na blacklist e access tokens emitidos anteriormente são recusados pelo cache compartilhado até expirarem. O usuário precisa entrar novamente com a nova senha.
- Configuração de produção adicionada ao `backend/.env`: `PUBLIC_FRONTEND_URL=https://www.salaopro.site` e `PASSWORD_RESET_TIMEOUT=1800`. Cópia privada anterior em `/root/backend-env-before-password-reset-20260928-010543`.
- Backup pré-publicação validado em `/root/salaopro-predeploy-20260928-010510`, contendo dump PostgreSQL e mídia compactada, ambos com verificação estrutural e hashes SHA-256.
- Validação: 82 testes backend aprovados (um ignorado), 11 testes frontend aprovados, lint e build aprovados. Na imagem candidata, os testes de link, uso único e revogação passaram com HTTPS desativado apenas no processo descartável; `nginx -t` passou.
- Somente backend e frontend foram recriados com `--no-deps`. Pós-publicação: nenhuma migração pendente, Gunicorn ativo, `DATABASE_OK=True`, Redis `PONG`, página inicial 200, página de redefinição 200, solicitação neutra com e-mail inexistente 200, API protegida 401 e painel 200.
- O teste automático em produção não enviou e-mail real: usou endereço inexistente. Fazer a confirmação visual final pelo botão “Esqueci minha senha” com uma conta autorizada e verificar recebimento, link, redefinição e novo login.

## Contador real de visitas (27/09/2026)

- Implementado e publicado no commit `6c8b666`. A landing page exibe “Plataforma em crescimento — X visitas reais”, sem valor inicial artificial.
- Cada aba/sessão do navegador registra no máximo uma visita por meio de `sessionStorage`. O backend mantém somente um total agregado na tabela `tenants_sitevisitcounter`; não armazena IP, identidade, user-agent ou histórico individual.
- O incremento usa operação atômica no banco e o endpoint público de escrita possui limitação por IP. `GET /api/site/visitas/` apenas consulta; `POST` incrementa.
- Backup pré-publicação validado em `/root/salaopro-predeploy-20260928-012405`, com dump PostgreSQL e mídia verificados e hashes SHA-256 registrados.
- Validação local: migrações sem divergência, 84 testes backend aprovados (um ignorado), 11 testes frontend aprovados, lint e build aprovados. Os dois testes específicos também passaram na imagem candidata.
- Somente backend e frontend foram recriados com `--no-deps`. A migração `tenants.0010_sitevisitcounter` foi aplicada com sucesso e criou o contador em zero.
- Pós-publicação: `DATABASE_OK=True`, Redis `PONG`, frontend 200, consulta pública do contador retornou `{"total":0}`, API protegida 401 e painel 200. A validação usou apenas GET e não aumentou artificialmente o total.

## Correção dos alertas falsos do WhatsApp (27/09/2026)

- A caixa de entrada estava recebendo a cada hora o assunto “URGENTE: WhatsApp Desconectado no Salão_PRO!” porque o cron executava `check_waha_status`, mas o `backend/.env` ainda apontava `WAHA_SESSION=default`. Essa sessão não existe no ambiente multiempresa.
- Em produção, `WAHA_SESSION` foi corrigido para `tenant_3`, a sessão principal atualmente conectada. Foi criada antes a cópia privada `/root/backend-env-before-waha-monitor-fix-20260928-013319`.
- Somente o container backend foi recriado, sem interromper ou recriar PostgreSQL, Redis, WAHA ou volumes.
- O mesmo comando usado pelo cron foi executado manualmente e confirmou: `WAHA está operando normalmente. Sessão 'tenant_3' conectada.` O monitor horário permanece ativo e agora só deve enviar e-mail se essa sessão realmente ficar indisponível.
- As mensagens antigas da caixa de entrada não foram apagadas.

## Endurecimento de segurança do navegador (27/09/2026)

- Foi preparada localmente a primeira etapa de baixo risco do reforço de segurança. O Nginx do frontend agora envia CSP restritiva, `Permissions-Policy`, `Referrer-Policy`, proteção contra MIME sniffing e enquadramento, isolamento de contexto e oculta a versão do servidor.
- A CSP permite somente os recursos usados atualmente: arquivos da própria aplicação, Google Fonts, imagens HTTPS e dados/blob necessários para avatares, QR codes e exportações. Scripts continuam limitados à própria origem.
- O Django passou a declarar explicitamente `nosniff`, referência restrita, isolamento de abertura entre origens e bloqueio total de frames.
- Validação local: 85 testes backend aprovados (um ignorado), 19 testes frontend aprovados, lint e build aprovados. `npm audit --omit=dev` encontrou zero vulnerabilidades nas dependências de produção.
- A migração dos tokens do `localStorage` para cookies `HttpOnly` não faz parte desta etapa; ela altera o fluxo completo de autenticação e deve ser implementada e homologada separadamente.
- `HSTS includeSubDomains/preload` permanece desativado até que todos os subdomínios sejam inventariados e confirmados com HTTPS, evitando indisponibilidade acidental.
