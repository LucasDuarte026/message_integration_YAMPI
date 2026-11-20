# Referência: Arquitetura do Message Integration

Bem-vindo à documentação de engenharia do projeto Message Integration Yampi. Este guia foi criado para desenvolvedores que precisam entender a infraestrutura subjacente, modificar o comportamento da máquina de estados ou solucionar problemas no sistema em execução.

## Explicação: Arquitetura e Limites dos Componentes

O projeto segue estritamente a **Clean Architecture (Arquitetura Hexagonal)**. As regras de negócio estão completamente isoladas da infraestrutura (bancos de dados, APIs, E-mail).

- `src/core/`: Infraestrutura interna, cliente HTTP (`client.py`), configurações globais (`config.py`), utilitários UTC-First (`time_utils.py`), logging seguro com Sentry (`logging_config.py`), telemetria Zero-Crash de disparos de e-mail (`telemetry.py`) e macros (`macros.py`).
- `src/domain/`: Contratos estritos (`interfaces.py`) e eventos de transição (`events.py`).
- `src/ports/`: Adaptadores para operações de I/O (persistência PostgreSQL com pool e `COALESCE(LEAST(...))` em `postgres_repo.py`, provedor SMTP stateful com roteamento dual `oficial@`/`comercial@` em `smtp_email_provider.py` e mock dry-run em `message_provider.py`).
- `src/services/`: Orquestração de notificações com escopos de telemetria (`notification_service.py`) e builders HTML/MJML (`email_builders/`).
- `src/templates/`: Templates MJML, assets visuais, `brand_data.yml` e HTMLs compilados.
- `src/workers/`: Rotinas concorrentes que executam os Casos de Uso (`orders.py` e `abandoned_cart.py`) usando `ThreadPoolExecutor`.
- `src/main.py` e `src/daemon.py`: Orquestradores que gerenciam dependências, liberação determinística de recursos com `flush_telemetry()` (`_close_resources` em `finally`) e ciclo contínuo com Sentry Crons.
- `src/webhook_server.py`: Servidor Flask para webhooks da Meta WhatsApp API.

## Explicação: A Máquina de Estados (STG / STC)

Para prevenir loops de mensagens, duplicação e spam, o sistema persiste o estado no PostgreSQL (`email_status_table` via `PostgresStateRepository`).
Cada Carrinho (STC) e Pedido (STG) passa por um ciclo de vida rigoroso em **UTC-First**:

### Máquina de Estados de Carrinho (STC)
- `STC 15`: Acionado após `4h` (`MACRO_CUPOM_CARRINHO_1_HORAS`) — Cupom 4 (10% OFF).
- `STC 16`: Acionado após `24h` (`MACRO_CUPOM_CARRINHO_2_HORAS`) — Cupom 5 (15% OFF).
- `STC 17`: Acionado após `48h` (`MACRO_CUPOM_CARRINHO_3_HORAS`) — Cupom 6 (20% OFF).
- `STC 18`: Acionado após `96h` (`MACRO_PERDIDO_CARRINHO_HORAS`) — Estado terminal (perdido).

### Máquina de Estados de Pedido (STG)
- `STG 1`: Pagamento aprovado de primeira (`is_paid`). Pode evoluir `1 → 3` ao entrar em `on_carriage` com código de rastreio.
- `STG 2`: Incentivo PIX/pagamento pendente (`5 min ≤ diff ≤ 30 min`).
- `STG 3`: Estado terminal concluído — envio de rastreio (`on_carriage`) ou confirmação pós-incentivo/cupom (exige código de rastreio presente).
- `STG 4 → 5 → 6 → 7 → 8`: Régua de recuperação para pedidos não pagos (`>30min` aguarda cupons; `24h` Cupom 1, `48h` Cupom 2, `72h` Cupom 3, `96h` perdido/reembolsado).

Quando uma entidade atinge um estado terminal (`STG ∈ {3, 8, 95, 96, 97}` ou `STC ∈ {18, 85, 86, 87}`), ou quando um carrinho converte em pedido (`order_id IS NOT NULL`), o worker correspondente ignora o registro em ciclos futuros.

## Referência: Configuração Avançada (.env & Macros)

A injeção de dependências e as feature flags são governadas pelo seu arquivo `.env` e pelo `src/core/macros.py`.

### Telemetria e Rastreamento de Erros
O daemon suporta relatórios de falhas resilientes e métricas de disparo de forma nativa:
- `SENTRY_DSN`: Endpoint para erros e métricas do Sentry, inicialização idempotente (`_SENTRY_INITIALIZED`), rastreamento distribuído APM (`TRACES_SAMPLE_RATE`) e `send_default_pii=False` (LGPD). Todas as exceções não tratadas e travamentos de thread são despachados automaticamente para o Sentry.
- **Application Metrics e Rastreamento SMTP ([`src/core/telemetry.py`](../src/core/telemetry.py))**: Emite contadores (`email.dispatch.started`, `email.dispatch.sent` após aceitação sem `refused` e `email.dispatch.failed`), span `email.smtp.send` por tentativa, breadcrumbs `smtp.retry` e captura de falhas preservando *traceback* completo com sanitização LGPD inclusive em `frame["vars"]`, drenando buffers ao final do ciclo via `flush_telemetry()`.

### Resiliência HTTP e Auto-Retries
O `YampiClient` inclui mecanismos automáticos de nova tentativa (retry) em rede transiente:
- **Max Retries**: Realiza até 3 tentativas com backoff exponencial para resets transientes de conexão (`ConnectionResetError`), timeouts de rede (`Timeout`), HTTP `429` ou erros de servidor HTTP `5xx` antes de lançar uma exceção.
- **Fail-Fast**: Erros de cliente não passíveis de nova tentativa (HTTP `4xx` não-429, como `401`/`404`) levantam exceção imediatamente sem novas tentativas.

### Disparo de E-mail Duplicado para Supervisão
Permite monitoramento em homologação ou produção através de e-mails duplicados em tempo real:
- **`MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH`**: Quando definido como `True` em `src/core/macros.py`, cada e-mail despachado para um cliente real aciona simultaneamente uma cópia enviada para `TEST_EMAIL_RECIPIENT` (configurado no `.env`). **Por padrão permanece `False` em produção** para evitar o acúmulo de cópias não lidas e prevenir sinais de *Graymail* na reputação do domínio.

## Tutorial: Como Rodar a Suíte de Testes

Antes de fazer o commit de qualquer modificação, garanta que a lógica principal permaneça intacta executando a suíte Pytest no ambiente virtual `.venv`:

```bash
# Execute toda a suíte com relatório de cobertura em src/
.venv/bin/python -m pytest --cov=src --cov-report=term-missing
```

## Documentação e Diagramas Visuais

Para uma referência completa de especificações SDD e fluxos visuais, consulte os documentos abaixo:

* 📜 **[Especificações Formais SDD (EARS + Cenários + ADRs)](./sdd_specs.md)**
* 🛡️ **[Políticas de Entregabilidade, Domínios e Governança Antispam (SDD)](./email_deliverability_policies.md)**
* 🏛️ [Arquitetura do Sistema & Clean Layers](./architecture.md)
* 🌳 [Árvore de Dependências do Projeto](./project_dependency_tree.md)
* 💻 [Especificações de Hardware e Limites de Recursos (Benchmarking)](./architecture.md#-especificação-de-hardware-e-dimensionamento-benchmarking)
* ⚙️ [Regras Temporais da Máquina de Estados](./email_state_machine.md)
* 📊 [Diagrama de Estados de Pedidos (STG)](./diagramas/stateDiagramOrders.md)
* 📊 [Diagrama de Estados de Carrinhos Abandonados (STC)](./diagramas/stateDiagramAbandonedCarts.md)
* 📡 [Especificação Técnica de Telemetria e Observabilidade (Sentry)](./sentry_dashboard_guide.md)
* 🧪 [Diretrizes de Testes (Pytest + TDD)](./testing_guidelines.md)
* 🐳 [Docker & Docker Compose Cheatsheet](./docker_cheatsheet.md)

---
*Para funcionalidades de negócio e dúvidas sobre licenciamento, consulte o [README Principal](../README.md).*
