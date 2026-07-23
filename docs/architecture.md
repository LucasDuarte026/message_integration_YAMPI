# Arquitetura e Diretivas Spec-Driven

Este documento descreve a infraestrutura não-monolítica e orientada a especificações (Spec-Driven Development) deste projeto. 
Ele serve como guia principal e mapa mental para agentes de IA e desenvolvedores que trabalham nesta base de código.

## 🚨 Diretiva Crítica de Manutenção (Para Agentes de IA e Desenvolvedores)
> [!CAUTION]
> **REGRA ESTRITA DE AUTO-DOCUMENTAÇÃO:**
> Sempre que for feito uma modificação, a documentação deve sofrer atualizações respectivas a essas mudanças.
> **SEMPRE QUE UM ARQUIVO FOR MODIFICADO, ADICIONADO OU REMOVIDO NESTE PROJETO:**
> Você **DEVE** atualizar imediatamente o arquivo `README.md` local do respectivo diretório onde a mudança ocorreu. Caso a mudança afete o fluxo geral, você deve atualizar este arquivo `architecture.md`. 
> A consistência e veracidade da documentação é um requisito estrito da nossa arquitetura Spec-Driven. Nunca escreva código sem documentar a mudança nos arquivos de documentação da pasta.

## Estrutura de Diretórios e Fluxo de Dados
O projeto adota uma variação de Clean Architecture / Hexagonal Architecture, dividida de forma que a Regra de Negócio não conheça os detalhes de Banco de Dados ou HTTP.

### 1. [`src/domain/`](../src/domain/README.md) (As Especificações)
O coração da aplicação. Não possui implementações, apenas contratos (`Protocols`, `Interfaces`, `ABC`). Tudo no sistema depende do domínio, mas o domínio não depende de nada. Se você vai criar uma funcionalidade nova, **comece especificando-a aqui**.

### 2. [`src/core/`](../src/core/README.md) (Infraestrutura Base e Clientes Internos)
Fornece os blocos de construção internos da nossa infraestrutura:
- Conexão e tratamento bruto com a API Yampi (`client.py`)
- Gerenciamento de credenciais via variáveis de ambiente (`config.py`)
- Repositório de estado / persistência local e relacional (`db.py` e `macros.py`)

### 3. [`src/ports/`](../src/ports/README.md) (Adaptadores Externos)
Onde as implementações de terceiros (que não são o nosso sistema core) vivem. Eles implementam os contratos do `domain`.
- Exemplo: Provedores de envio de mensagens via WhatsApp/Email (SMTP, Mocks).
- Exemplo: Implementação do banco de dados relacional (PostgreSQL via `postgres_repo.py`).

### 4. [`src/workers/`](../src/workers/README.md) (Regras de Negócio e Use Cases)
Os sub-programas que executam as atividades (ex: Recuperação de Carrinho Abandonado e Atualização de Pedidos). Os workers são isolados, não instanciam conexões e devem receber todas as dependências (Core e Ports) injetadas no construtor pelo Orquestrador.
> **NOTA:** A lógica de estado (STG e STC) processada pelos workers é estritamente regida pela **[Lógica e Máquina de Estados de E-mails](./email_state_machine.md)**. Qualquer mudança na regra de negócio deve primeiro ser modelada naquele documento.

### 5. `src/main.py` (Orquestrador / Ponto de Entrada)
É quem junta tudo. Ele importa as configurações, cria a instância do banco de dados, a instância da API, e as passa como dependência para o Worker desejado. É desenhado para ser executado via CLI (ex: `crontab`).

### 6. `src/webhook_server.py` (Servidor de Webhooks)
Servidor Flask independente que escuta na porta 5000 para receber validações de token (GET) e payloads de mensagens/status em tempo real (POST) vindos da Meta API.
