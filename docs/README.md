# Referência: Arquitetura do Message Integration

Bem-vindo à documentação de engenharia do projeto Message Integration Yampi. Este guia foi criado para desenvolvedores que precisam entender a infraestrutura subjacente, modificar o comportamento da máquina de estados ou solucionar problemas no sistema em execução.

## Explicação: Arquitetura e Limites dos Componentes

O projeto segue estritamente a **Clean Architecture (Arquitetura Hexagonal)**. As regras de negócio estão completamente isoladas da infraestrutura (bancos de dados, APIs, E-mail).

- `src/core/`: Entidades de domínio, configurações globais (`config.py`) e feature flags fixas (`macros.py`).
- `src/domain/`: Casos de uso lidando com a lógica específica de mensagens (ex: Carrinhos Abandonados, Pedidos Pendentes).
- `src/ports/`: Interfaces para operações de I/O (persistência de estado em SQLite, telemetria Sentry, clientes HTTP da API Yampi e SMTP).
- `src/workers/`: Rotinas concorrentes que executam periodicamente os Casos de Uso usando `ThreadPoolExecutor`.
- `src/daemon.py`: O orquestrador principal que gerencia o ciclo de vida e o tempo das threads.

## Explicação: A Máquina de Estados (STG / STC)

Para prevenir loops de mensagens, duplicação e spam, o sistema persiste o estado em um banco de dados SQLite local (`state.db`).
Cada Carrinho (STC) e Pedido (STG) passa por um ciclo de vida rigoroso:

### Máquina de Estados de Carrinho (STC)
- `STC1`: Acionado em 15 minutos (10% de desconto).
- `STC2`: Acionado em 24 horas (15% de desconto).
- `STC3`: Acionado em 72 horas (20% de desconto).

### Máquina de Estados de Pedido (STG)
- `PIX_PENDING`: Acionado 30 minutos após a criação do pedido se não for pago.
- `PIX_APPROVED`: Acionado após a confirmação do pagamento.
- `ON_CARRIAGE`: Acionado quando o pacote é despachado, enviando informações de rastreio.

Quando uma entidade atinge um estado terminal (ex: carrinho convertido ou decorridas 72h), ela transita para `completed` (concluído) e é ignorada em todos os loops futuros.

## Referência: Configuração Avançada (.env & Macros)

A injeção de dependências e as feature flags são governadas pelo seu arquivo `.env` e pelo `macros.py`.

### Telemetria e Rastreamento de Erros
O daemon suporta relatórios de falhas resilientes de forma nativa:
- `SENTRY_DSN`: Endpoint para erros do Sentry e rastreamento distribuído APM (`TRACES_SAMPLE_RATE`). Todas as exceções não tratadas e travamentos de thread são despachadas automaticamente para o Sentry.

### Resiliência HTTP e Auto-Retries (v6.3.0)
O `YampiClient` inclui mecanismos automáticos de nova tentativa (retry) em rede transiente:
- **Max Retries**: Realiza até 3 tentativas com backoff exponencial para resets transientes de conexão (`ConnectionResetError`), timeouts de rede (`Timeout`) ou erros de servidor HTTP 5xx antes de lançar uma exceção.
- **Fail-Fast**: Erros de cliente não passíveis de nova tentativa (HTTP 4xx como 401/404) levantam exceção imediatamente sem novas tentativas.

### Disparo de E-mail Duplicado para Supervisão (v6.3.0)
Permite monitoramento em produção através de e-mails duplicados em tempo real:
- **`MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH`**: Quando definido como `True` em `macros.py`, cada e-mail despachado para um cliente real em produção aciona simultaneamente uma cópia enviada para `TEST_EMAIL_RECIPIENT` (`deutschlucas026@gmail.com`) para auditoria em tempo real.

## Tutorial: Como Rodar a Suíte de Testes

Antes de fazer o commit de qualquer modificação, garanta que a lógica principal permaneça intacta executando os testes unitários:

```bash
# Ative seu ambiente virtual
source venv/bin/activate

# Descubra e rode todos os testes unitários
python3 -m unittest discover -s tests
```

## Diagramas Visuais

Para uma referência visual de como os componentes se comunicam entre si, veja os diagramas Mermaid abaixo:

* 🏛️ [Arquitetura do Sistema & Clean Layers](./architecture.md)
* 💻 [Especificações de Hardware e Limites de Recursos (Benchmarking)](./architecture.md#-especificação-de-hardware-e-dimensionamento-benchmarking)
* ⚙️ [Regras Temporais da Máquina de Estados](./email_state_machine.md)
* 📊 [Diagrama de Estados de Pedidos (STG)](./diagramas/stateDiagramOrders.md)
* 📊 [Diagrama de Estados de Carrinhos Abandonados (STC)](./diagramas/stateDiagramAbandonedCarts.md)

---
*Para funcionalidades de negócio e dúvidas sobre licenciamento, consulte o [README Principal](../README.md).*
