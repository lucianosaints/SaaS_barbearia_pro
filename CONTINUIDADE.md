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
