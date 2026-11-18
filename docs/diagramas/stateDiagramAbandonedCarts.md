# Diagrama de Estados — STC (Carrinhos Abandonados)

**Data de Criação:** 2026-07-21  
**Referência:** [email_state_machine.md](../email_state_machine.md) | [Índice de Diagramas](./README.md)

---

## Legenda

- **Referência temporal (UTC-First)**: `diff = get_now_utc() - data_carrinho` (derivada de `updated_at` com fallback `created_at`, protegida via `COALESCE(LEAST(...))` e normalizada para UTC a partir do banco)
- **Condição de entrada**: o worker de carrinhos **só processa** registros com e-mail válido onde `order_id IS NULL`
- **Congelamento**: quando `order_id` é preenchido, o STC **congela** no valor que está e nunca mais é alterado pelo worker de carrinhos
- **Círculos duplos** `[*]`: estados terminais (`stc ∈ {18, 85, 86, 87}`)

---

## Diagrama

```mermaid
stateDiagram-v2
    direction TB

    [*] --> NULL_C : Carrinho Criado na Yampi (STC = null)

    state "Novo Carrinho [STC = null]" as NULL_C
    state "Email Cupom 4: Lembrete com Link de Recuperação<br/>(STC = 15)" as EC4
    state "Email Cupom 5: Recuperação de Carrinho<br/>(STC = 16)" as EC5
    state "Email Cupom 6: Última Chance de Recuperação<br/>(STC = 17)" as EC6
    state "Carrinho Abandonado Perdido<br/>(STC = 18 ✗)" as ST18
    state "Email Agradecimento Conversão<br/>(STC = 85/86/87)" as S8X

    state order_check <<choice>>
    NULL_C --> order_check : Worker de Carrinhos verifica order_id
    order_check --> SKIP : order_id preenchido (carrinho virou pedido)
    order_check --> EC4 : order_id IS NULL e diff > 4h

    state "STC Congelado (Carrinho Virou Pedido)" as SKIP

    EC4 --> EC5 : diff > 24h desde o carrinho
    EC5 --> EC6 : diff > 48h desde o carrinho
    EC6 --> ST18 : diff > 96h desde o carrinho

    note right of SKIP : STC congela no estado atual.<br/>Worker de Carrinhos ignora.<br/>STG assume o registro.
    note right of ST18 : ESTADO TERMINAL<br/>Esgotou cupons de carrinho (sistema pula)
    note left of S8X : FUTURO (Futura Implementação)<br/>Carrinho abandonado → converteu em pedido

    ST18 --> [*]

```

---

## Tabela Resumo de Transições

| De | Para | Condição Temporal | Condição Extra | Email | Terminal? |
|---|---|---|---|---|---|
| `null` | `15` | `diff > 4h` | `order_id IS NULL` | Cupom 4 + link `simulate_url` | Não |
| `15` | `16` | `diff > 24h` | `order_id IS NULL` | Cupom 5 + link `simulate_url` | Não |
| `16` | `17` | `diff > 48h` | `order_id IS NULL` | Cupom 6 + link `simulate_url` | Não |
| `17` | `18` | `diff > 96h` | `order_id IS NULL` | — | ✓ Sim |

---

## Cenário de Congelamento (Carrinho → Pedido)

```mermaid
sequenceDiagram
    participant Yampi as API Yampi
    participant WC as Worker Carrinhos
    participant DB as email_status_table
    participant WP as Worker Pedidos

    Note over DB: cart_id=ABC, stc=15, order_id=NULL

    WC->>DB: BUSCA cart_id=ABC
    DB-->>WC: stc=15, order_id=NULL
    WC->>WC: diff > 24h? SIM
    WC->>DB: UPDATE stc=16 ✓

    Note over Yampi: Cliente finaliza compra!

    WP->>DB: BUSCA cart_id=ABC (via pedido.metadata.cart_id)
    DB-->>WP: ENCONTROU (stc=16)
    WP->>DB: UPDATE order_id=XYZ, data_pedido=..., cpf=..., sku=...
    Note over DB: cart_id=ABC, stc=16 (congelado), order_id=XYZ, stg=NULL

    WC->>DB: BUSCA cart_id=ABC
    DB-->>WC: order_id=XYZ (não é NULL)
    WC->>WC: SKIP ❌ (não processa mais)

    WP->>DB: BUSCA cart_id=ABC
    DB-->>WP: stg=NULL → aplica lógica STG normalmente ✓
```

---

## Emails de Carrinho Abandonado vs Pedido

| Aspecto | Cupons 1/2/3 (STG) | Cupons 4/5/6 (STC) |
|---|---|---|
| **Estrutura HTML** | Base padrão | Base padrão (similar) |
| **Texto** | Referência ao pedido | Menção explícita de carrinho abandonado |
| **Botão de ação** | Link genérico da loja | Link `simulate_url` (recuperação do checkout) |
| **Objetivo** | Recuperar pagamento pendente | Fazer o cliente voltar e finalizar o carrinho |

---

## Regra de Entrada do Worker de Carrinhos

```
PARA CADA carrinho elegível (updated_at || created_at <= 15 dias e com e-mail):
  1. cart_id ← carrinho.id
  2. data_carrinho ← updated_at || created_at (convertido para UTC)
  3. UPSERT cart_id na email_status_table (FOR UPDATE + COALESCE(LEAST(data_carrinho)))
     ├── EXISTE:
     │   ├── order_id IS NOT NULL → SKIP
     │   └── order_id IS NULL → prosseguir
     └── NÃO EXISTE → INSERT nova linha
                        (cart_id, order_number='N/A', data_carrinho, cpf, sku, stc=NULL, order_id=NULL)
  4. Normalizar row["data_carrinho"] para UTC e LER stc
  5. SE stc ∈ {18, 85, 86, 87} → SKIP
  6. APLICAR transições conforme tabela acima
  7. SE email enviado com sucesso (True) → update_stc + timestamp_ultimo_email (UTC) + breadcrumb
     SE envio retornar False → abortar update_stc (retentativa no próximo ciclo)
```
