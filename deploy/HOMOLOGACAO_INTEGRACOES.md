# Homologacao de Nginx, WAHA, SMTP e Mercado Pago

Atualizado em 22/09/2026. Nenhuma verificacao deste documento autoriza publicacao direta em producao.

## Resultado local

- Rate limit: producao usa `django.core.cache.backends.redis.RedisCache` no endereco interno `redis://redis:6379/1`. O Compose inclui Redis sem porta publicada, limite de memoria e healthcheck; o backend aguarda o cache ficar saudavel.
- Nginx: configuracao e rotas foram revisadas; lint e build do frontend passaram. O daemon Docker local nao estava ativo e o executavel Nginx nao esta instalado, portanto `nginx -t` ainda deve ser executado na imagem candidata.
- WAHA: chave e senhas deixaram de ficar gravadas no Compose. A chamada interna, cabecalho `X-Api-Key`, sessao por empresa, telefone e timeout foram testados com API simulada.
- SMTP: configuracao incoerente TLS+SSL agora e recusada; producao exige host, usuario, senha e remetente. Destinatarios de alerta usam `EMAIL_ALERT_TO`. O envio de alerta foi testado com backend de e-mail em memoria.
- Mercado Pago: o usuario confirmou que a integracao de producao ja funciona. Pagamentos continuam explicitamente desabilitados no Compose candidato com `PERMITIR_PAGAMENTOS=False` ate a homologacao. A criacao exige administrador, aceita somente 1, 3, 6 ou 12 meses e cria uma cobranca local com referencia opaca. O webhook consulta a API, confere cobranca, valor e moeda e processa cada cobranca uma unica vez.

## Verificacoes aprovadas

- 7 testes dedicados de integracao.
- Suite Django: testes funcionais aprovados; os 8 testes do entrypoint passaram separadamente fora do sandbox Windows.
- Frontend: lint, 7 testes Vitest e build de producao aprovados.
- `makemigrations --check --dry-run`, `manage.py check` e `git diff --check` aprovados.

## Etapa obrigatoria em homologacao conectada

1. Rotacionar as credenciais WAHA antigas, pois estiveram no historico Git. Configurar `WAHA_API_KEY`, `WAHA_ADMIN_USER` e `WAHA_ADMIN_PASSWORD` fora do repositorio.
2. Subir a imagem candidata isolada e executar `nginx -t`. Testar `/`, `/api/`, `/painel-master/`, `/estaticos/` e `/arquivos/` pela cadeia TLS completa.
3. Conectar uma sessao WAHA de teste e enviar mensagens somente a numeros autorizados. Confirmar persistencia de `waha_data` apos reinicio.
4. Usar uma caixa SMTP de homologacao. Confirmar STARTTLS ou SSL conforme o provedor, remetente autorizado, entrega, rejeicao e timeout sem expor credenciais em logs.
5. Usar credenciais TEST do Mercado Pago e manter `PERMITIR_PAGAMENTOS=False` ate o ensaio. Aplicar a migracao `payments.0001_initial`, habilitar temporariamente e testar PIX aprovado, pendente, rejeitado e webhook repetido.
6. Somente depois do ensaio definir as credenciais de producao e a URL publica do webhook no painel Mercado Pago.

### Rotacao coordenada do WAHA

Gerar novos valores fora do repositorio, atualizar o `.env` do Compose no servidor e recriar somente `waha` e `backend`. Os dois servicos precisam receber a mesma `WAHA_API_KEY`; usuario e senha do painel ficam somente no servico WAHA. Nao usar `docker compose down`, nao remover `waha_data` e nao imprimir o `.env`. Depois da recriacao, validar a sessao existente e uma mensagem para numero autorizado antes de invalidar qualquer acesso operacional antigo.

## Criterios de bloqueio

- Nao publicar sem backup/restauracao verificados e sem aplicar a nova migracao.
- Nao reutilizar a credencial WAHA anteriormente versionada.
- Nao usar token Mercado Pago de producao em testes automatizados.
- Nao imprimir `.env`, tokens, chaves, senhas ou corpos integrais de respostas externas.
