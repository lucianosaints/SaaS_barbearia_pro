# Recuperação da definição do PostgreSQL

## Situação verificada

O banco está em execução, mas o Compose atual e a revisão `ca9b786` não definem o serviço `db`, mesmo incluindo todos os perfis. A busca textual no histórico disponível desse arquivo não encontrou commits alterando a declaração `db:`. Não há definição anterior recuperada; não presumir que o container possa ser recriado pelo Compose atual.

## Dados que a proposta deve preservar

| Item | Valor confirmado |
| --- | --- |
| Projeto / serviço registrados | `saas_barbearia_pro` / `db` |
| Container | `barbeiro_pro_db` |
| Família da imagem | `postgres:15-alpine`; ID exato pendente |
| Volume existente | `saas_barbearia_pro_postgres_data` |
| Destino do volume | `/var/lib/postgresql/data` |
| Rede existente | `saas_barbearia_pro_barbeiro_pro_net` |
| Aliases do banco | `db`, `barbeiro_pro_db` |
| Endereço usado pelo Django | `db:5432` |
| Clientes externos | Nenhum, conforme usuário |

## Proposta e verificações pendentes

1. Recuperar os parâmetros necessários do container ativo: imagem exata, reinício, usuário, memória compartilhada, PGDATA e opções de inicialização. Não compartilhar dumps completos de `docker inspect`, variáveis ou comandos que possam conter senhas.
2. Preservar credenciais e configurações sensíveis no servidor, em arquivos protegidos fora do Git. A configuração da aplicação e as credenciais efetivas do banco precisam permanecer compatíveis; não gerar uma senha nova incidentalmente nessa recuperação.
3. Preparar um arquivo candidato separado, com o serviço `db`, alias interno e referências explícitas aos recursos existentes. Preferir declarar o volume existente como externo na proposta para impedir a criação silenciosa de um volume vazio por mudança de nome. Conferir as definições globais atuais antes de integrar a rede/volume ao Compose.
4. O serviço proposto não precisa publicar 5432 no host: a aplicação usa `db:5432` na rede Docker. A aplicação dessa mudança exige planejamento de uma breve indisponibilidade do banco; não confundir editar um arquivo com mudar o container ativo.
5. Validar o candidato sem iniciá-lo. Conferir o banco efetivo da aplicação, fazer backup lógico e testar restauração em ambiente separado. Preservar também mídia e dados WAHA, além da configuração anterior necessária para retorno.
6. Somente depois preparar a substituição controlada do container, mantendo o volume e sem atualizar a versão do PostgreSQL ao mesmo tempo. Não usar `down --volumes`, limpeza de volumes ou `--remove-orphans` para resolver a divergência.

Este documento é um plano, não um Compose pronto para implantação. Nenhuma recriação, mudança de porta ou alteração de dados foi executada.
