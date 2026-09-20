# Atualização de produção

Esta versão foi preparada e verificada localmente. O ambiente informado é Vultr, com PostgreSQL no mesmo servidor e domínio https://www.salaopro.site. Somente os endpoints públicos do site foram consultados: a página respondeu HTTP 200 por Nginx, e /api/ respondeu HTTP 401 com autenticação Bearer. Nenhum acesso administrativo ou alteração de produção foi realizado. Consulte também [VULTR_POSTGRESQL.md](VULTR_POSTGRESQL.md).

## O que mudou

**Pendência de implantação identificada em 20/09/2026:** o Compose do servidor não lista `db`, mesmo incluindo todos os perfis, embora `barbeiro_pro_db` esteja ativo e registre origem nesse mesmo arquivo. Recuperar e revisar a definição do PostgreSQL antes de publicar ou alterar sua porta. Preservar `saas_barbearia_pro_postgres_data` e a rede existente. Não executar `--remove-orphans` ou `down` durante esse diagnóstico. Detalhes e próxima consulta em `CONTINUIDADE.md`.

- Escritas de usuários e serviços exigem administrador da empresa ou superusuário. A consulta pública de profissionais retorna somente identificação, nome, empresa e tipo, sem e-mail, senha ou campos administrativos.
- A empresa enviada em parâmetros de consulta não permite editar registros de outra barbearia.
- Clientes criam reservas para si e podem cancelar as próprias reservas futuras. Profissionais consultam a agenda da empresa e alteram somente seus atendimentos. Administradores operam a agenda da empresa.
- Reservas são gravadas em transação, com verificação de serviços, empresa, profissional ativo, expediente, almoço, data futura e sobreposição. A linha do profissional é bloqueada no PostgreSQL; no SQLite, transações de escrita usam IMMEDIATE.
- Estados permitidos: PENDENTE → CONFIRMADO ou CANCELADO; CONFIRMADO → CONCLUIDO ou CANCELADO. Somente atendimentos já iniciados podem ser concluídos. CONCLUIDO e CANCELADO são finais; correções de registros históricos precisam de procedimento administrativo específico.
- O painel de gestão ganhou ações Confirmar, Concluir e Cancelar.
- A conclusão fixa total, comissão e saldo com Decimal e arredondamento de centavos. A taxa padrão continua em 40%, respeitando a taxa individual entre 0 e 100%. O campo chamado lucro líquido continua sendo total menos comissão; despesas, impostos e taxas de pagamento não são deduzidos.
- Alterar somente o início do agendamento também recalcula seu término.
- Exclusão por API foi desativada para preservar histórico. Serviços, empresas e usuários devem ser desativados. O Django admin foi reservado a superusuários globais; agendamentos ficam somente para consulta nessa interface e são gerenciados pela API/painel.
- Senhas novas passam pelos validadores do Django. Senhas existentes não são reescritas.
- Renovação JWT usa o endereço configurado da API, compartilha renovações concorrentes e invalida o refresh antigo. A blacklist exige as migrações indicadas abaixo.
- A notificação de agendamento ocorre depois do commit e já contém os serviços. Falhas de SMTP são registradas sem desfazer a reserva. A interface não promete entrega de e-mail.
- DEBUG fica desligado por padrão. Em produção, chave secreta e hosts explícitos são obrigatórios.
- Dependências reproduzíveis: backend/requirements.lock e frontend/package-lock.json.

## Compatibilidade e decisões a conferir antes da liberação

Os bloqueios de transição, o cancelamento do cliente somente antes do início, a edição do profissional apenas da própria agenda e o acesso global ao Django admin são restrições novas. Verifique se a operação atual usa outro fluxo antes de publicar.

Integrações que usavam DELETE, alteravam status livremente ou liam e-mail/username no catálogo público deverão ser adaptadas. Campos de resposta de agendamento existentes foram preservados e nomes/valor total foram acrescentados.

Não há migração automática de dados legados nem alteração do esquema dos modelos de negócio nesta versão. Não recrie o banco e não execute seed.py em produção. As tabelas novas são as do aplicativo token_blacklist. Não há troca automática de SQLite para PostgreSQL.

A gravação validada deve passar pela API. Scripts com acesso direto ao ORM/SQL precisam respeitar as mesmas regras; não existe constraint de exclusão de intervalos no banco nesta versão. A auditoria ajuda a localizar registros antigos incompatíveis.

## Configuração

Consulte backend/.env.example e frontend/.env.example. São exemplos: os arquivos não são lidos automaticamente. Configure o ambiente do serviço ou o mecanismo de variáveis da hospedagem.

Preserve a chave secreta atual se ela já for segura e tiver pelo menos 50 caracteres. Uma troca de chave encerra sessões e invalida tokens anteriores. Se necessário, gere uma chave com:

```sh
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Nunca publique a chave ou credenciais no Git. Use DEBUG=False, hosts explícitos, URLs HTTPS em CORS/CSRF e o banco persistente que já está em produção. Em produção, DB_ENGINE=postgresql, DB_NAME, DB_USER e DB_HOST agora são obrigatórios. A aplicação recusa iniciar em SQLite ou com essas informações ausentes. Em desenvolvimento (DEBUG=True), SQLite continua disponível.

Com proxy reverso, habilite DJANGO_TRUST_PROXY somente se o proxy remover o X-Forwarded-Proto recebido do cliente e inserir seu próprio valor. Caso contrário, o redirecionamento HTTPS pode falhar ou ser contornado. HSTS de subdomínios/preload só deve ser habilitado quando todos os domínios envolvidos já atendem HTTPS.

VITE_API_URL é incorporada no build; mudar apenas o ambiente do servidor depois do build não altera o frontend. Configure a origem da API sem /api e sem barra final. Vazio em produção usa o mesmo domínio.

O SMTP é configurável. Sem configuração, o backend padrão escreve e-mails no console, sem entregá-los. Os logs podem conter dados de clientes; configure acesso e retenção.

## Ensaio em homologação

Use uma cópia protegida do banco real, com envio de e-mail desabilitado ou redirecionado para caixa de testes. Não aponte a suíte de testes para as credenciais de produção.

Na raiz, com Python 3.11+ e Node 22.12+:

```sh
python -m venv .venv
# Windows (PowerShell):
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock
.\.venv\Scripts\python.exe -m pip check
# Linux: use .venv/bin/python nos dois comandos anteriores.
```

Os comandos abaixo usam python do ambiente virtual ativo. No PowerShell, é possível usar o executável diretamente, sem mudar a política de execução.

```sh
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py auditar_agenda --fail-on-issues
python manage.py collectstatic --noinput
python manage.py check --deploy
```

A auditoria é somente leitura e informa IDs, sem imprimir dados pessoais. Ela verifica vínculos entre empresas, perfis, períodos inválidos, sobreposições e valores financeiros incompletos. Caso encontre problemas, revise cada registro com o responsável antes de liberar. Não reconstitua comissões antigas pela taxa atual sem conferir o histórico.

Para testes locais em PowerShell, com banco temporário separado:

```powershell
$env:DJANGO_DEBUG = 'True'
$env:TEST_DATABASE_NAME = Join-Path $PWD 'test-concurrency.sqlite3'
..\.venv\Scripts\python.exe manage.py test --noinput
```

TEST_DATABASE_NAME deve apontar EXCLUSIVAMENTE para um arquivo descartável de testes. O Django cria e destrói esse banco. Em SQLite sem essa variável, o teste de concorrência é pulado porque o banco em memória não reproduz o comportamento do arquivo. Para homologação PostgreSQL, execute a mesma suíte com credenciais exclusivas de teste e permissão para criar o banco de testes.

No frontend:

```sh
cd frontend
npm ci
npm run lint
npm test
npm run build
npm audit
```

No PowerShell com scripts bloqueados, use npm.cmd. O resultado está em frontend/dist. Sirva esses arquivos pelo servidor web; não use o servidor de desenvolvimento Vite em produção.

Teste na homologação: cadastro/login, reserva, segunda tentativa simultânea no mesmo horário, cancelamento liberando vaga, confirmação/conclusão e atualização financeira, acesso de outro cliente/empresa e renovação após expirar o access token.

## Aplicação da versão

1. Registre a versão anterior, o pacote de dependências, as variáveis e o artefato frontend em uso.
2. Faça backup consistente do banco e teste sua restauração. Para SQLite, pause gravações e use o mecanismo de backup do SQLite, ou faça a cópia com a aplicação parada. Para PostgreSQL, use a ferramenta de backup da hospedagem/pg_dump. Proteja também os arquivos persistentes.
3. Coloque o sistema em manutenção e pare os processos antigos que gravam reservas. Misturar versões antigas e novas durante a atualização deixa caminhos sem as validações novas.
4. Instale requirements.lock em um ambiente virtual da nova versão e npm ci no ambiente de build. Mantenha o banco e as variáveis existentes, aplicando as novas configurações explicitamente.
5. Execute migrate --plan, migrate --noinput, auditar_agenda --fail-on-issues, collectstatic --noinput e check --deploy.
6. Publique frontend/dist junto com o backend atualizado, inicie o serviço e execute o teste operacional descrito acima.
7. Libere o tráfego e acompanhe erros, recusas de reserva, autenticação e SMTP.

O servidor WSGI Waitress foi instalado para execução multiplataforma. Um exemplo, a partir de backend, atrás de um proxy HTTPS, é:

```sh
waitress-serve --listen=127.0.0.1:8000 core.wsgi:application
```

Adapte o comando à hospedagem e mantenha-o sob o gerenciador de processos existente. WhiteNoise atende os estáticos do Django após collectstatic. O frontend deve ser servido como arquivos estáticos, com encaminhamento correto de /api e /admin.

Agende python manage.py flushexpiredtokens diariamente para limpar tokens expirados. O limite de tentativas de autenticação usa o cache local do Django nesta versão; para múltiplas instâncias, aplique também limite no proxy/gateway ou configure cache compartilhado.

## Retorno à versão anterior

Antes de liberar gravações, é possível parar a versão nova e voltar ao artefato/código/dependências/configuração anterior mantendo as tabelas extras de blacklist, que são aditivas. Não reverta migrações de negócio nem apague tabelas para esse retorno.

Se já houver reservas novas, preserve-as. Não restaure um backup antigo indiscriminadamente: isso perderia os atendimentos criados depois dele. Pare as gravações, compare os dados e planeje a reconciliação antes de restaurar. A versão antiga também volta a expor suas falhas anteriores; mantenha manutenção/restrição de acesso até decidir a correção.

## Verificação local e limites

Após a verificação abaixo, o entrypoint recebido de produção foi corrigido localmente e oito testes adicionais de fluxo shell passaram, em execução separada com comandos Python/Gunicorn simulados. O entrypoint novo interrompe falhas de migração/coleta de estáticos. A integração com Docker/volumes ainda depende das configurações de produção pendentes; consulte deploy/BACKEND_BUILD.md.

Resultado local: 30 testes do backend aprovados, incluindo seis verificações de configuração do banco. Os seis testes do frontend, lint, build, pip check e npm audit passaram na etapa anterior, sem alterações posteriores no código frontend. O Django check --deploy passou com variáveis de produção de teste, incluindo HSTS para subdomínios/preload habilitado nesse ensaio. A checagem de migrações dos modelos de negócio não encontrou mudanças pendentes. O build emitiu um aviso de tamanho de bundle JavaScript (aproximadamente 757 kB, 232 kB comprimido), sem impedir a geração. Os testes de transação executados localmente ainda usaram SQLite; a execução real em PostgreSQL permanece pendente.

A suíte inclui isolamento por empresa, perfil, conflitos, horários, cancelamento, comissão, rollback, e-mails, JWT, duas requisições concorrentes, auditoria sem alterações e proteção do Django admin. O frontend verifica renovação de sessão, fila de requisições, logout e seleção entre empresas.

A concorrência foi verificada com SQLite em arquivo. PostgreSQL, proxy, SMTP real, backup e restauração da produção ainda precisam ser testados na infraestrutura utilizada. O Docker local não estava com o daemon disponível. O arquivo compose.test.yml prepara uma execução isolada dos testes em PostgreSQL 15 Alpine, conforme a imagem informada em produção; sua configuração foi validada, mas os containers ainda não foram executados. Confira a versão real e as instruções em VULTR_POSTGRESQL.md. O build e os testes não substituem esse ensaio.

Referências: [checklist de implantação do Django](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/), [bloqueios de consultas](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update), [permissões do DRF](https://www.django-rest-framework.org/api-guide/permissions/).
