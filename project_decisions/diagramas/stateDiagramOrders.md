# Diagrama de Estados — STG (Pedidos)

**Data de Criação:** 2026-07-21  
**Referência:** [email_state_machine.md](../../docs/email_state_machine.md)

---

## Legenda

- **Referência temporal**: `diff = now() - data_pedido` (sempre absoluto)
- **Círculos duplos** `[*]`: estados terminais (sistema pula na próxima iteração)
- **Condições entre colchetes**: lógica verificada pelo worker de pedidos
- **Ações entre parênteses**: email enviado e/ou marcação no banco

---

## Diagrama

```mermaid
stateDiagram-v2
    direction TB

    [*] --> NULL : Novo Pedido no BD (STG = null)

    state "Novo Pedido [STG = null]" as NULL
    state "Email 1: Confirmação de Pagamento<br/>(STG = 1 ✓)" as E1
    state "Email 2: Incentivo ao Pagamento + PIX<br/>(STG = 2)" as E2
    state "Email 3: Confirmação Tardia de Pagamento<br/>(STG = 3 ✓)" as E3
    state "Aguardando Janela de Cupons<br/>(STG = 4)" as ST4
    state "Email Cupom 1: 10% Desconto<br/>(STG = 5)" as EC1
    state "Email Cupom 2: 15% Desconto<br/>(STG = 6)" as EC2
    state "Email Cupom 3: 20% Desconto<br/>(STG = 7)" as EC3
    state "Cliente Perdido<br/>(STG = 8 ✗)" as ST8
    state "Email Recompra<br/>(STG = 95/96/97)" as REC

    NULL --> E1 : diff ≤ 30min e Pagamento Aprovado
    NULL --> E2 : diff ≤ 30min e Pagamento Pendente
    NULL --> ST4 : diff > 30min e Pagamento Não Aprovado

    E2 --> E3 : Pagamento Aprovado
    E2 --> ST4 : diff > 30min e Pagamento Não Aprovado

    ST4 --> EC1 : diff > 24h desde o pedido
    EC1 --> EC2 : diff > 48h desde o pedido
    EC2 --> EC3 : diff > 72h desde o pedido
    EC3 --> ST8 : diff > 96h desde o pedido

    note right of E1 : ESTADO TERMINAL<br/>Pagou de primeira (sistema pula)
    note right of E3 : ESTADO TERMINAL<br/>Pagou após PIX (sistema pula)
    note right of ST8 : ESTADO TERMINAL<br/>Esgotou 3 cupons (sistema pula)
    note left of REC : FUTURO (Futura Implementação)<br/>Recompra detectada por CPF + SKU

    E1 --> [*]
    E3 --> [*]
    ST8 --> [*]

```

---

## Tabela Resumo de Transições

| De | Para | Condição Temporal | Condição de Pagamento | Email | Terminal? |
|---|---|---|---|---|---|
| `null` | `1` | `diff ≤ 30min` | Aprovado | Email 1 | ✓ Sim |
| `null` | `2` | `diff ≤ 30min` | Pendente | Email 2 | Não |
| `null` | `4` | `diff > 30min` | Não aprovado | — | Não |
| `2` | `3` | qualquer | Aprovado | Email 3 | ✓ Sim |
| `2` | `4` | `diff > 30min` | Não aprovado | — | Não |
| `4` | `5` | `diff > 24h` | — | Cupom 1 (10%) | Não |
| `5` | `6` | `diff > 48h` | — | Cupom 2 (15%) | Não |
| `6` | `7` | `diff > 72h` | — | Cupom 3 (20%) | Não |
| `7` | `8` | `diff > 96h` | — | — | ✓ Sim |


---

## Caminhos Completos Possíveis

```mermaid
flowchart LR
    A["Caminho A\n(melhor caso)"] --> A1["null → 1"]
    B["Caminho B\n(pagou após PIX)"] --> B1["null → 2 → 3"]
    C["Caminho C\n(timeout direto)"] --> C1["null → 4 → 5 → 6 → 7 → 8"]
    D["Caminho D\n(timeout via incentivo)"] --> D1["null → 2 → 4 → 5 → 6 → 7 → 8"]

    style A1 fill:#22c55e,color:#fff
    style B1 fill:#22c55e,color:#fff
    style C1 fill:#ef4444,color:#fff
    style D1 fill:#ef4444,color:#fff
```

---

## Regra de Entrada do Worker de Pedidos

```
PARA CADA pedido no JSON:
  1. cart_id ← pedido.metadata.cart_id
  2. BUSCAR cart_id na email_status_table
     ├── EXISTE → UPDATE pedido_id, data_pedido, cpf, sku
     └── NÃO EXISTE → INSERT nova linha
  3. LER stg
  4. SE stg ∈ {1, 3, 8, 95, 96, 97} → SKIP
  5. APLICAR transições conforme tabela acima
  6. SE email enviado → sobrescrever timestamp_ultimo_email
  7. COMMIT (dentro de transação FOR UPDATE)
```
