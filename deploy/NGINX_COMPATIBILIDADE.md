# Compatibilidade com o Nginx recebido

A referência está em `references/frontend.nginx.production.conf`. Foram removidas somente as cercas Markdown da mensagem e normalizada a formatação. Não foi instalada no servidor nem validada com `nginx -t`.

## Ajustes locais

- Com `DJANGO_DEBUG=False`, Django usa `/painel-master/` para admin e `/estaticos/` para os estáticos servidos pelo WhiteNoise.
- Em desenvolvimento, permanecem `/admin/` e `/static/`.
- Mídia usa `/arquivos/` e `BASE_DIR/media`, que corresponde a `/app/media` no container. `MEDIA_DIRECTORY` permite configurar a mesma pasta usada pelo entrypoint.
- Isso não acrescenta campos de upload ausentes no código local nem implementa o fallback de mídia do Django usado pela instalação atual. Comparar o código de produção antes de atualizar.

## Pendências para publicar

1. Mounts confirmados: backend e frontend compartilham `saas_barbearia_pro_django_media` em `/app/media`, ambos com escrita. Ainda conferir conteúdo/permissões e backup/restauração das fotos. Propor somente leitura no frontend após conferir o Compose. O backend também monta `/root/SaaS_barbearia_pro/backend` em `/app`; isso sobrepõe o código da imagem.
2. Portas confirmadas: frontend em `0.0.0.0:3000` e `[::]:3000`; backend somente em `127.0.0.1:8000`. Conferir firewalls e configuração do Nginx do host, que aparentemente termina o TLS, antes de restringir o frontend ao loopback. O proxy interno força `X-Forwarded-Proto https` para API/admin, mas não define esse cabeçalho para estáticos ou fallback de mídia. Com redirecionamento HTTPS ativo no Django, essa diferença pode causar redirecionamentos repetidos. Verificar a cadeia completa antes de definir cabeçalhos confiáveis ou ativar `DJANGO_TRUST_PROXY`.
3. Não substituir automaticamente esse cabeçalho por `$scheme`: o Nginx interno escuta HTTP, embora a conexão externa possa ser HTTPS.
4. Verificar se `/arquivos/` contém somente mídia pública antes de manter o cache público por 30 dias.
5. Após preparar a configuração final, validar com `nginx -t` em ambiente isolado e testar admin, CSS, API e fotos através do proxy completo.

Documentação: https://docs.djangoproject.com/en/5.2/ref/settings/#secure-proxy-ssl-header e https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_set_header.

Nenhuma configuração do servidor foi alterada nesta etapa.
