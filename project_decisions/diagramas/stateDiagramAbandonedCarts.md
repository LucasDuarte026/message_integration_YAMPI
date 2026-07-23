# Diagrama de Estados — STC (Carrinhos Abandonados)

**Data de Criação:** 2026-07-21  
**Referência:** [email_state_machine.md](../../docs/email_state_machine.md)

---

## Legenda

- **Referência temporal**: `diff = now() - data_carrinho` (sempre absoluto)
- **Condição de entrada**: o worker de carrinhos **só processa** registros onde `pedido_id IS NULL`
- **Congelamento**: quando `pedido_id` é preenchido, o STC **congela** no valor que está e nunca mais é alterado pelo worker de carrinhos
- **Círculos duplos** `[*]`: estados terminais (sistema pula na próxima iteração)

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

    state pedido_check <<choice>>
    NULL_C --> pedido_check : Worker de Carrinhos verifica pedido_id
    pedido_check --> SKIP : pedido_id preenchido (carrinho virou pedido)
    pedido_check --> EC4 : pedido_id IS NULL e diff > 4h

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
| `null` | `15` | `diff > 4h` | `pedido_id IS NULL` | Cupom 4 + link `simulate_url` | Não |
| `15` | `16` | `diff > 24h` | `pedido_id IS NULL` | Cupom 5 + link `simulate_url` | Não |
| `16` | `17` | `diff > 48h` | `pedido_id IS NULL` | Cupom 6 + link `simulate_url` | Não |
| `17` | `18` | `diff > 96h` | `pedido_id IS NULL` | — | ✓ Sim |

---

## Cenário de Congelamento (Carrinho → Pedido)

```mermaid
sequenceDiagram
    participant Yampi as API Yampi
    participant WC as Worker Carrinhos
    participant DB as email_status_table
    participant WP as Worker Pedidos

    Note over DB: cart_id=ABC, stc=15, pedido_id=NULL

    WC->>DB: BUSCA cart_id=ABC
    DB-->>WC: stc=15, pedido_id=NULL
    WC->>WC: diff > 24h? SIM
    WC->>DB: UPDATE stc=16 ✓

    Note over Yampi: Cliente finaliza compra!

    WP->>DB: BUSCA cart_id=ABC (via pedido.metadata.cart_id)
    DB-->>WP: ENCONTROU (stc=16)
    WP->>DB: UPDATE pedido_id=XYZ, data_pedido=..., cpf=..., sku=...
    Note over DB: cart_id=ABC, stc=16 (congelado), pedido_id=XYZ, stg=NULL

    WC->>DB: BUSCA cart_id=ABC
    DB-->>WC: pedido_id=XYZ (não é NULL)
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
PARA CADA carrinho no JSON:
  1. cart_id ← carrinho.id
  2. BUSCAR cart_id na email_status_table
     ├── EXISTE:
     │   ├── pedido_id IS NOT NULL → SKIP
     │   └── pedido_id IS NULL → prosseguir
     └── NÃO EXISTE → INSERT nova linha
                        (cart_id, data_carrinho, cpf, sku, stc=NULL)
                        (pedido_id=NULL, data_pedido=NULL, stg=NULL)
  3. LER stc
  4. SE stc ∈ {18, 85, 86, 87} → SKIP
  5. APLICAR transições conforme tabela acima
  6. SE email enviado → sobrescrever timestamp_ultimo_email
  7. COMMIT (dentro de transação FOR UPDATE)
```
