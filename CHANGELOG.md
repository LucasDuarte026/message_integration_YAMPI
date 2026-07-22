# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Unreleased / 2.0.0] - Planejado (Refatoração de Lógica de E-mails)

### Adicionado / Em Planejamento (Especificação em [04_refactor_logic_emails.md](file:///home/luska/Documents/projects/message_integration/project_decisions/04_refactor_logic_emails.md))
- **Tabela Unificada (`email_status_table`)**: Substituição das tabelas separadas `cart_states` e `order_states` por esquema unificado por `cart_id`.
- **Máquina de Estados Dupla**:
  - **STG (Status Global)**: Controle do fluxo de pedidos (`null, 1, 2, 3, 4, 5, 6, 7, 8, 95, 96, 97`).
  - **STC (Status Carrinho)**: Controle do fluxo de carrinhos abandonados (`null, 15, 16, 17, 18, 85, 86, 87`).
- **Timers Temporais Absolutos**: Cálculos temporais baseados diretamente em `data_pedido` (STG) ou `data_carrinho` (STC).
- **Processamento Assíncrono em Lote**: Produtor consulta Yampi e divide resultados em arquivos JSON de 100 itens (`orders/` e `carts/`), consumidos e deletados por workers paralelos.
- **Locking Concorrente**: Leitura e gravação no banco com `SELECT FOR UPDATE` para evitar corrupção por acesso simultâneo.
- **Bloco de Macros (`MACRO_*`)**: Configuração centralizada no topo dos arquivos de código para prazos, tamanhos de lote e intervalos.
- **Diagramas de Estado Mermaid**:
  - `project_decisions/diagramas/stateDiagramOrders.md`
  - `project_decisions/diagramas/stateDiagramAbandonedCarts.md`

---

## [1.0.0] - 2026-07-21 (Versão Atual / Baseline Estável)

### Adicionado
- **Integração Yampi REST API v2**:
  - Autenticação e consulta de pedidos (`/v2/{alias}/orders`) e carrinhos abandonados (`/v2/{alias}/checkout/carts`).
  - Scripts de teste e coleta (`estudos/yampi_api/coleta.sh`).
- **Arquitetura Hexagonal (Ports & Adapters)**:
  - Interfaces no domínio (`src/domain/`).
  - Adaptadores SMTP (`src/ports/smtp_email_provider.py`), WhatsApp Meta Cloud API (`src/ports/whatsapp_meta_provider.py`) e DryRun (`src/ports/message_provider.py`).
- **Persistência de Estado Local (SQLite / PostgreSQL Inicial)**:
  - Controle básico de e-mails já enviados para evitar disparos duplicados.
- **Infraestrutura Docker**:
  - `Dockerfile` e `docker-compose.yml` para execução isolada com PostgreSQL.
- **Servidor Webhook Flask**:
  - Micro-serviço para recepção e validação de Webhooks Meta/WhatsApp (`src/webhook_server.py`).
- **Documentação Decisória de Arquitetura**:
  - Decisões de projeto organizadas em `project_decisions/` (`01_database_yampi_planning.md`, `02_email_architecture.md`, `03_mudanca_arquitetura_emails_e_geral.md`).
