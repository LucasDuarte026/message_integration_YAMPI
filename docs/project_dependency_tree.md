# Árvore de Dependências e Arquitetura do Projeto

Este documento detalha o mapa de dependências de alto nível do sistema, seguindo os princípios estabelecidos na documentação de Clean Architecture e Spec-Driven Development. A regra de ouro é: **A Regra de Negócio (Workers/Domain) não depende de detalhes externos (Banco/APIs); os detalhes externos implementam contratos do domínio.**

## 1. Diagrama de Injeção de Dependências (Hexagonal Architecture)

```mermaid
graph TD
    %% Centro do Sistema (Sem Dependências)
    subgraph DOMAIN ["1. Especificações (Core Absoluto)"]
        D_INT["src/domain/interfaces.py"]
    end

    subgraph INFRA ["2. Infraestrutura e Adaptadores Externos"]
        C_CONF["src/core/config.py"]
        C_MACR["src/core/macros.py"]
        C_LOGS["src/core/logging_config.py"]
        C_CLIE["src/core/client.py <br> YampiClientProtocol"]
        P_PG["src/ports/postgres_repo.py <br> StateRepositoryProtocol"]
        P_SMTP["src/ports/smtp_email_provider.py <br> MessageProviderProtocol"]
    end

    %% Regras de Negócio (Dependem do Domain e Macros)
    subgraph WORKERS ["3. Casos de Uso / Regras de Negócio"]
        W_CART["src/workers/abandoned_cart.py <br> AbandonedCartProcessor"]
        W_ORD["src/workers/orders.py <br> OrderProcessor"]
    end

    %% Ponto de Entrada (Conhece Tudo)
    subgraph ENTRY ["4. Orquestrador / Entrypoint"]
        M_MAIN["src/main.py"]
        M_WEB["src/webhook_server.py"]
    end

    %% Relações de Dependência
    C_CLIE -. Implementa .-> D_INT
    P_PG -. Implementa .-> D_INT
    P_SMTP -. Implementa .-> D_INT
    
    W_CART --> D_INT
    W_ORD --> D_INT
    W_CART --> C_MACR
    W_ORD --> C_MACR

    %% Injeção de Dependências feita pelo Main
    M_MAIN ==>|1. Lê Credenciais| C_CONF
    M_MAIN ==>|2. Instancia| C_CLIE
    M_MAIN ==>|3. Instancia| P_PG
    M_MAIN ==>|4. Instancia| P_SMTP
    
    M_MAIN ==>|5. Injeta Dependências| W_CART
    M_MAIN ==>|5. Injeta Dependências| W_ORD
```

---

## 2. Fluxo Estrutural de Injeção (Passo a Passo)

A hierarquia de dependências flui de fora (Entrypoint) para dentro (Domain), garantindo desacoplamento total.

### Nível 1: O Domínio (`src/domain/`)
- **Quem é:** O coração da aplicação (ex: `interfaces.py`).
- **Do que depende:** De ninguém.
- **O que faz:** Dita as regras do jogo. Define os `Protocols` que qualquer banco de dados, provedor de email ou cliente Yampi deve obedecer se quiser existir no sistema.

### Nível 2: Infraestrutura (`src/core/` e `src/ports/`)
- **Quem são:** `client.py` (Yampi), `postgres_repo.py` (PostgreSQL), `smtp_email_provider.py` (SMTP), `logging_config.py` (Logs).
- **Do que dependem:** Do `domain/` (para herdar/implementar os contratos) e de bibliotecas externas (`psycopg2`, `requests`, `smtplib`, `logging`).
- **O que fazem:** Lidam com o mundo real (Internet, Banco de Dados, APIs, Saída de Sistema).

### Nível 3: Casos de Uso (`src/workers/`)
- **Quem são:** `abandoned_cart.py` e `orders.py`.
- **Do que dependem:** Estritamente do `domain/` (recebem instâncias no construtor com os *type hints* das interfaces) e de `core/macros.py` (para usar as variáveis de tempo estipuladas na lógica de negócio).
- **O que fazem:** Executam a **Máquina de Estados de E-mails (STG/STC)**, lendo dados, tomando decisões lógicas e pedindo para enviar e-mails. Não sabem se estão escrevendo no SQLite ou no Postgres, nem se estão mandando e-mail ou WhatsApp.

### Nível 4: Entrypoints (`src/main.py`)
- **Quem é:** O roteador principal, geralmente engatilhado por um Cron ou manualmente.
- **Do que depende:** De **todos** os módulos.
- **O que faz:** Ele é a "fábrica". Lê o `.env` do `config.py`, cria o banco `PostgresRepo()`, cria o `YampiClient()`, cria o `SMTPProvider()`, junta tudo isso no construtor do `OrderProcessor(client, repo, provider)` e finalmente aperta o botão `processor.execute()`.
