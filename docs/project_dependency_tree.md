# Árvore de Dependências e Arquitetura do Projeto

Este documento detalha o mapa de dependências de alto nível do sistema, seguindo os princípios estabelecidos na documentação de Clean Architecture e Spec-Driven Development. A regra de ouro é: **A Regra de Negócio (Workers/Domain) não depende de detalhes externos (Banco/APIs); os detalhes externos implementam contratos do domínio.**

## 1. Diagrama de Injeção de Dependências (Hexagonal Architecture)

```mermaid
graph TD
    %% Centro do Sistema (Sem Dependências)
    subgraph DOMAIN ["1. Especificações (Core Absoluto)"]
        D_INT["src/domain/interfaces.py"]
        D_EVT["src/domain/events.py"]
    end

    subgraph INFRA ["2. Infraestrutura, Serviços e Adaptadores Externos"]
        C_CONF["src/core/config.py"]
        C_MACR["src/core/macros.py"]
        C_TIME["src/core/time_utils.py"]
        C_LOGS["src/core/logging_config.py"]
        C_TELE["src/core/telemetry.py <br> Sentry Metrics & Scrubbing"]
        C_CLIE["src/core/client.py <br> YampiClientProtocol"]
        P_PG["src/ports/postgres_repo.py <br> StateRepositoryProtocol"]
        P_SMTP["src/ports/smtp_email_provider.py <br> MessageProviderProtocol"]
        P_DRY["src/ports/message_provider.py <br> DryRunMessageProvider"]
        S_NOTIF["src/services/notification_service.py <br> & email_builders/"]
    end

    %% Regras de Negócio (Dependem do Domain, Time e Macros)
    subgraph WORKERS ["3. Casos de Uso / Regras de Negócio"]
        W_CART["src/workers/abandoned_cart.py <br> AbandonedCartProcessor"]
        W_ORD["src/workers/orders.py <br> OrderProcessor"]
    end

    %% Ponto de Entrada (Conhece Tudo)
    subgraph ENTRY ["4. Orquestrador / Entrypoint"]
        M_DAEMON["src/daemon.py <br> Sentry Crons 5m"]
        M_MAIN["src/main.py <br> _close_resources() in finally"]
        M_WEB["src/webhook_server.py"]
    end

    %% Relações de Dependência
    C_CLIE -. Implementa .-> D_INT
    P_PG -. Implementa .-> D_INT
    P_SMTP -. Implementa .-> D_INT
    P_DRY -. Implementa .-> D_INT
    
    W_CART --> D_INT
    W_ORD --> D_INT
    W_CART --> D_EVT
    W_ORD --> D_EVT
    W_CART --> C_MACR
    W_ORD --> C_MACR
    W_CART --> C_TIME
    W_ORD --> C_TIME
    W_CART --> S_NOTIF
    W_ORD --> S_NOTIF
    S_NOTIF --> D_EVT
    S_NOTIF --> C_TELE
    P_SMTP --> C_TELE
    M_MAIN --> C_TELE

    %% Injeção de Dependências feita pelo Main
    M_DAEMON ==>|Loop 300s| M_MAIN
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
- **Quem é:** O coração da aplicação (`interfaces.py` e `events.py`).
- **Do que depende:** De ninguém.
- **O que faz:** Dita as regras do jogo. Define os `Protocols` (`YampiClientProtocol`, `MessageProviderProtocol`, `StateRepositoryProtocol`) e os DTOs (`OrderTransitionEvent`, `CartTransitionEvent`).

### Nível 2: Infraestrutura e Serviços (`src/core/`, `src/ports/` e `src/services/`)
- **Quem são:** `client.py` (Yampi), `time_utils.py` (UTC-First), `postgres_repo.py` (PostgreSQL com pool e `COALESCE(LEAST(...))`), `smtp_email_provider.py` (SMTP stateful com roteamento dual `oficial@`/`comercial@`, `close()` e telemetria), `message_provider.py` (Dry-Run), `logging_config.py` (`SafeRotatingFileHandler` + Sentry idempotente), `telemetry.py` (contadores Sentry Zero-Crash, spans SMTP, escopos thread-safe e sanitização LGPD) e `notification_service.py` + `email_builders/` (renderização MJML/Jinja2).
- **Do que dependem:** Do `domain/` e de bibliotecas externas (`psycopg2`, `requests`, `smtplib`, `jinja2`, `PyYAML`, `sentry-sdk`, `logging`).
- **O que fazem:** Lidam com o mundo real (Internet, Banco de Dados, E-mail, Renderização, Telemetria e Logs).

### Nível 3: Casos de Uso (`src/workers/`)
- **Quem são:** `abandoned_cart.py` e `orders.py`.
- **Do que dependem:** Estritamente do `domain/` (interfaces e eventos), `core/macros.py`, `core/time_utils.py` e `services/notification_service.py`.
- **O que fazem:** Executam a **Máquina de Estados de E-mails (STG/STC)**, normalizando timestamps em UTC retornados pelo banco, tomando decisões lógicas e acionando notificações com rollback fail-safe em caso de falha de envio.

### Nível 4: Entrypoints (`src/main.py`, `src/daemon.py` e `src/webhook_server.py`)
- **Quem são:** Os roteadores e orquestradores principais.
- **Do que dependem:** De **todos** os módulos necessários para montar o grafo de dependências.
- **O que fazem:** `src/main.py` lê `config.py`, instancia `PostgresStateRepository`, `YampiClient` e `SMTPEmailProvider`/`DryRunMessageProvider`, injeta-os nos workers e garante o encerramento das conexões e o envio dos buffers de telemetria (`_close_resources()` + `flush_telemetry()`) em bloco `finally`. `src/daemon.py` executa `run_all()` a cada 300s com Sentry Crons.
