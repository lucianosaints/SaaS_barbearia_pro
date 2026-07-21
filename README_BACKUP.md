# Rotina de Backup Automático

O sistema possui um comando customizado do Django para gerar o backup do banco de dados (seja PostgreSQL ou SQLite), compactá-lo em `.zip` e enviá-lo por e-mail para `infor@salaopro.site`.

## Como Configurar no Crontab (Linux / VPS)

Para que o backup ocorra automaticamente todos os dias às 03:00 da manhã, você precisa agendar o comando no `crontab` do servidor host onde o Docker está rodando.

### Passo 1: Descobrir o nome do container
Primeiro, verifique o nome do container do backend do Django executando:
```bash
docker ps
```
*(Geralmente é algo como `salaopro-backend-1` ou `backend`)*

### Passo 2: Editar o Crontab
Abra o agendador de tarefas cron do seu servidor (host) executando:
```bash
crontab -e
```

### Passo 3: Adicionar a rotina
Adicione a linha abaixo no final do arquivo, substituindo `<nome_do_container>` pelo nome real do seu container do Django:

```cron
0 3 * * * docker exec -i <nome_do_container> python manage.py send_backup >> /var/log/salaopro_backup.log 2>&1
```

*Nota: Em rotinas do crontab, geralmente não podemos usar a flag `-t` (tty) no `docker exec`, por isso usamos apenas `-i` ou rodamos sem as flags iterativas.*

### O que essa rotina faz?
- `0 3 * * *`: Executa todos os dias às 03:00 AM.
- `docker exec ...`: Executa o comando dentro do container rodando sem precisar pará-lo.
- `>> /var/log/salaopro_backup.log 2>&1`: Salva o log da execução do comando em um arquivo no host para você monitorar se houve sucesso ou falha, gravando saídas padrão (stdout) e erros (stderr).

---

# Rotina de Monitoramento do WhatsApp (WAHA)

O sistema também possui um comando customizado para monitorar se a API do WhatsApp está conectada. Caso a sessão caia ou o servidor pare, um e-mail de emergência será disparado para `infor@salaopro.site`.

### Como Configurar no Crontab

Para rodar essa verificação **de hora em hora**, adicione a seguinte linha no seu `crontab -e`:

```cron
0 * * * * cd /root/SaaS_barbearia_pro && docker compose exec -T backend python manage.py check_waha_status >> /var/log/salaopro_waha_check.log 2>&1
```

### O que essa rotina faz?
- `0 * * * *`: Executa no minuto zero de todas as horas (de hora em hora).
- `docker compose exec -T ...`: Executa o comando via compose sem alocar um pseudo-TTY (ideal para scripts agendados).
- Caso detecte que o WAHA não está rodando ou a sessão não está conectada (`WORKING`), envia um e-mail imediatamente para o admin reler o QR Code.
