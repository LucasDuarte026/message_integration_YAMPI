# Lógica e Máquina de Estados de E-mails

Este documento define formalmente a máquina de estados STG/STC, o schema unificado da tabela de tracking, contratos de workers, macros configuráveis e regras de concorrência para o sistema de processamento de mensagens.


## 1. Visão Geral

O sistema de emails opera como uma **máquina de estados dupla** com dois eixos independentes:

- **STG (Status Global)** — governa o fluxo de emails para **pedidos** (orders).
- **STC (Status Carrinho)** — governa o fluxo de emails para **carrinhos abandonados** (abandoned carts).

Ambos coexistem **na mesma linha** da tabela unificada `email_status_table`, são processados por workers independentes, e requerem **locking exclusivo** para evitar corrupção por acesso concorrente.

O objetivo desta especificação é servir de **contrato de implementação** para a futura refatoração do código, sem ambiguidades.

---

## 2. Macros Configuráveis

Todas as constantes temporais e de paginação devem ser declaradas como variáveis `MACRO_` no topo do arquivo principal, com comentários descritivos. Isso permite ajuste centralizado sem buscar valores espalhados pelo código.

```python
# ============================================================
# MACROS DE CONFIGURAÇÃO — alterar apenas aqui
# ============================================================

# --- Execução e Consulta ---
MACRO_INTERVALO_EXECUCAO_SEG = 300       # 5 min — intervalo entre ciclos do sistema
MACRO_JANELA_CONSULTA_HORAS = 48         # horas de histórico consultadas na API Yampi
MACRO_TAMANHO_PAGINA = 100               # itens por página na consulta à API Yampi

# --- Timers de Pedido (STG) — referência: data_pedido ---
MACRO_TIMEOUT_PAGAMENTO_SEG = 1800       # 30 min — janela máxima de incentivo de pagamento inicial
MACRO_DELAY_ORDER_PIX_EMAIL_SEG = 300    # 5 min — gordurinha/delay mínimo antes de disparar o Email 2 (PIX)
MACRO_CUPOM_PEDIDO_1_HORAS = 12          # STG 4→5 — email cupom 1 (10%)
MACRO_CUPOM_PEDIDO_2_HORAS = 14          # STG 5→6 — email cupom 2 (15%)
MACRO_CUPOM_PEDIDO_3_HORAS = 16          # STG 6→7 — email cupom 3 (20%)

MACRO_PERDIDO_PEDIDO_HORAS = 18          # STG 7→8 — cliente perdido

# --- Timers de Carrinho Abandonado (STC) — referência: data_carrinho ---
MACRO_CUPOM_CARRINHO_1_HORAS = 14        # STC null→15 — email cupom 4 + link recuperação
MACRO_CUPOM_CARRINHO_2_HORAS = 16        # STC 15→16  — email cupom 5 + link recuperação
MACRO_CUPOM_CARRINHO_3_HORAS = 18        # STC 16→17  — email cupom 6 + link recuperação
MACRO_PERDIDO_CARRINHO_HORAS = 20        # STC 17→18  — cliente perdido
```

---

## 3. Schema do Banco de Dados — `email_status_table`

### 3.1 Definição SQL

```sql
CREATE TABLE IF NOT EXISTS email_status_table (
    cart_id                 VARCHAR(255)   PRIMARY KEY,
    order_id                VARCHAR(255)   DEFAULT NULL,
    order_number            VARCHAR(255)   NOT NULL DEFAULT 'N/A',
    data_pedido             TIMESTAMP      DEFAULT NULL,
    data_carrinho           TIMESTAMP      DEFAULT NULL,
    cpf                     VARCHAR(14)    NOT NULL,
    sku                     VARCHAR(255)   NOT NULL,
    stg                     INTEGER        DEFAULT NULL,
    stc                     INTEGER        DEFAULT NULL,
    timestamp_ultimo_email  TIMESTAMP      DEFAULT NULL
);

-- Índice para busca O(1) de recompra por CPF
CREATE INDEX IF NOT EXISTS idx_email_status_cpf ON email_status_table (cpf);

-- Índice para busca O(1) de recompra por CPF + SKU
CREATE INDEX IF NOT EXISTS idx_email_status_cpf_sku ON email_status_table (cpf, sku);

-- Índice para busca O(1) por número público do pedido
CREATE INDEX IF NOT EXISTS idx_email_status_order_number ON email_status_table (order_number);
```

### 3.2 Regras dos Campos

| Coluna | Tipo | Restrição | Descrição |
|---|---|---|---|
| `cart_id` | `VARCHAR(255)` | **PK**, nunca vazio | ID do carrinho na Yampi. É a chave porque todo pedido nasce de um carrinho. |
| `order_id` | `VARCHAR(255)` | Pode ser `NULL` | ID interno do pedido na Yampi. Preenchido quando o carrinho se converte em pedido. |
| `order_number` | `VARCHAR(255)` | **NOT NULL** (Default `'N/A'`) | Número público de transação do pedido Yampi/Shopify (ex: `1200388456451468`). |
| `data_pedido` | `TIMESTAMP` | Pode ser `NULL` | Timestamp da criação do pedido na Yampi. Base temporal para cálculos de STG. |
| `data_carrinho` | `TIMESTAMP` | Pode ser `NULL` | Timestamp da criação do carrinho na Yampi. Base temporal para cálculos de STC. |
| `cpf` | `VARCHAR(14)` | **NOT NULL** | CPF do cliente. Usado em busca O(1) para detecção de recompra (status 99). |
| `sku` | `VARCHAR(255)` | **NOT NULL** | SKU do produto de maior valor do pedido/carrinho. Segundo critério da busca de recompra. |
| `stg` | `INTEGER` | Default `NULL` | Status Global — fluxo de pedidos. Valores: `NULL, 1, 2, 3, 4, 5, 6, 7, 8, 95, 96, 97`. |
| `stc` | `INTEGER` | Default `NULL` | Status Carrinho Abandonado — fluxo de carrinhos. Valores: `NULL, 15, 16, 17, 18, 85, 86, 87`. |
| `timestamp_ultimo_email` | `TIMESTAMP` | Pode ser `NULL` | **Metadado puro.** Sobrescrito a cada email enviado. Nunca usado como base de cálculo temporal. |

---

## 4. Máquina de Estados — STG (Pedidos)

### 4.1 Referência Temporal

**IMPORTANTE (Fuso Horário):** Todos os cálculos, timestamps e registros no banco de dados **devem** ser feitos no fuso horário **UTC-3 (Horário de Brasília / São Paulo)**. Como a API da Yampi também costuma retornar dados nesse fuso, usar UTC-3 garante que não haja defasagem no disparo de cupons. No código Python, deve-se extrair o `now` usando compensação de -3 horas ou timezone apropriado.

Todos os cálculos temporais de STG usam:

```python
now_utc3 = datetime.utcnow() - timedelta(hours=3)
diff_pedido = now_utc3 - data_pedido
```

### 4.2 Tabela de Transições

| De | Para | Condição | Ação | Email |
|---|---|---|---|---|
| Qualquer (`!= 3, 8`) | `3` | Status Yampi `on_carriage` **E** Código de Rastreio presente | Enviar email de rastreio, marcar STG=3 | **Envio Rastreio**: Notificação de transporte + código `{tracking_code}` e link `{tracking_url}` |
| `null` | `1` | Pagamento aprovado (`paid`, `in_separation`, `invoiced`) | Enviar email, marcar STG=1 | **Email 1**: Confirmação de pagamento |
| `null` | `2` | `diff ≤ 30 min` e pagamento **pendente** (`waiting_payment`, `created`, `authorized`) | Enviar email, marcar STG=2 | **Email 2**: Confirmação de pedido + incentivo ao pagamento + PIX/QR Code |
| `null` | `4` | `diff > 30 min` e pagamento **NÃO** aprovado | Marcar STG=4 (sem email nessa transição, o cupom 1 sai em 24h) | — |
| `2, 4, 5, 6, 7` | `3` | Pagamento aprovado (`paid`, `in_separation`, `invoiced`) **E** Código de Rastreio presente | Enviar email, marcar STG=3 | **Email 3**: Confirmação de pagamento |
| Qualquer | `8` | Pedido reembolsado (`refunded`) | Marcar STG=8 | — (cliente perdido/reembolsado) |
| `2` | `4` | `diff > 30 min` e pagamento **NÃO** aprovado (incluindo `cancelled` por PIX expirado) | Marcar STG=4 | — |
| `4` | `5` | `diff > 12h` e pagamento **NÃO** aprovado | Enviar email, marcar STG=5 | **Email Cupom 1**: desconto dinâmico (ex: 10%) via `brand_data.yml` |
| `5` | `6` | `diff > 14h` e pagamento **NÃO** aprovado | Enviar email, marcar STG=6 | **Email Cupom 2**: desconto dinâmico (ex: 15%) via `brand_data.yml` |
| `6` | `7` | `diff > 16h` e pagamento **NÃO** aprovado | Enviar email, marcar STG=7 | **Email Cupom 3**: desconto dinâmico (ex: 20%) via `brand_data.yml` |
| `7` | `8` | `diff > 18h` e pagamento **NÃO** aprovado | Marcar STG=8 | — (cliente perdido, terminal) |

### 4.3 Estados Terminais (STG)

Quando o sistema encontra um registro com um destes valores de STG, **pula sem processar**:

| STG | Significado |
|---|---|
| `3` | Pagamento e despacho concluídos (E-mail de rastreio ou confirmação final enviado) |
| `8` | Cliente perdido / Pedido cancelado |
| `95` | Recompra detectada (future implementation) |
| `96` | Recompra detectada (future implementation) |
| `97` | Recompra detectada (future implementation) |

### 4.4 Fluxos Possíveis (Caminhos Completos)

```
Caminho A (pago de primeira):     null → 1 → 3                     (confirmado de primeira → despachado no 3)
Caminho B (despachado direto):   null → 3                         (on_carriage direto na Yampi)
Caminho C (pagou após PIX):      null → 2 → 3                     (incentivo PIX funcionou)
Caminho D (recuperado no cupom): null → 2 → 4 → 5 → ... → 3      (cupons funcionaram, virou pago/despachado)
Caminho E (timeout direto):      null → 4 → 5 → 6 → 7 → 8        (nunca pagou, >30min no 1o check)
Caminho F (timeout via 2):       null → 2 → 4 → 5 → 6 → 7 → 8   (incentivado, mas nunca pagou)
```

---

## 5. Máquina de Estados — STC (Carrinhos Abandonados)

### 5.1 Condição de Entrada

O worker de carrinhos abandonados **só processa** registros onde:

```python
order_id IS NULL   # carrinho ainda não virou pedido
```

Se `order_id` está preenchido → **pular completamente**. O STC fica congelado no valor que está.

### 5.2 Referência Temporal

Todos os cálculos temporais de STC usam:

```python
diff_carrinho = now() - data_carrinho
```

### 5.3 Tabela de Transições

| De | Para | Condição | Ação | Email |
|---|---|---|---|---|
| `null` | `15` | `diff > 14h` do abandono | Enviar email, marcar STC=15 | **Email Cupom 4**: desconto dinâmico (ex: 10%) + link recuperação |
| `15` | `16` | `diff > 16h` do abandono | Enviar email, marcar STC=16 | **Email Cupom 5**: desconto dinâmico (ex: 15%) + link recuperação |
| `16` | `17` | `diff > 18h` do abandono | Enviar email, marcar STC=17 | **Email Cupom 6**: desconto dinâmico (ex: 20%) + link recuperação |
| `17` | `18` | `diff > 20h` | Marcar STC=18 | — (cliente perdido, terminal) |

### 5.4 Estados Terminais (STC)

| STC | Significado |
|---|---|
| `18` | Cliente perdido (esgotou cadeia de cupons de carrinho, 20h) |
| `85` | Conversão de carrinho abandonado → pedido (future implementation) |
| `86` | Conversão de carrinho abandonado → pedido (future implementation) |
| `87` | Conversão de carrinho abandonado → pedido (future implementation) |

### 5.5 Emails de Carrinho vs Emails de Pedido

Os emails cupons 4, 5 e 6 (STC) são para **carrinhos** e possuem:
1. **Texto**: Menção explícita de que o carrinho foi abandonado.
2. **Botão de ação**: O link do botão aponta para `simulate_url` (link de recuperação do checkout Yampi), levando o cliente de volta ao carrinho com produtos e dados preenchidos.

Já os cupons 1, 2 e 3 (STG) são para **pedidos** não pagos:
1. **Texto**: Focam em informar que o pagamento não foi concluído e oferecem um cupom para um **novo pedido**.
2. **Sem botão de recuperação**: Não apontam de volta ao pedido, pois o PIX/Boleto original pode já ter sido cancelado/vencido.

---

## 6. Interação entre STG e STC — Coexistência

### 6.1 Princípio Fundamental

STG e STC são **eixos independentes** na mesma linha da tabela. Cada worker é responsável por apenas um eixo:

| Worker | Atua sobre | Origem dos dados | Regra de Execução / Filtragem |
|---|---|---|---|
| **Worker de Pedidos** | Coluna `stg` | Arquivos JSON de `orders/` | **Sempre executa** ao consumir um pedido. Lê o `stg` atual (seja `null` ou já iniciado), interpreta o estado do pedido na Yampi e toma as decisões de envio/transição. Só pula se o `stg` for terminal (`1, 3, 8, 95, 96, 97`). Independe completamente do valor de `stc`. |
| **Worker de Carrinhos** | Coluna `stc` | Arquivos JSON de `carts/` | **Executa apenas se `order_id IS NULL`**. Se o registro já possui `order_id` preenchido (o carrinho se converteu em pedido), o worker de carrinhos ignora o registro e não altera o `stc`. |


### 6.2 Cenário: Carrinho Abandonado Vira Pedido

Quando o worker de pedidos encontra um pedido cujo `cart_id` já existe na tabela (com STC preenchido):

1. **Vincula** `order_id` e `data_pedido` à linha existente.
2. **Atualiza** `cpf` e `sku` (pode ter mudado).
3. **NÃO altera** `stc` — o valor fica congelado no estado que estava (15, 16 ou 17).
4. O `stg` começa em `null` e segue o fluxo normal de pedidos.
5. O worker de carrinhos **nunca mais** processará este registro (pois `order_id` não é mais `NULL`).

> **Nota para future implementation**: O valor congelado de STC será usado no futuro para inferir se o cliente voltou a comprar motivado pelo cupom de carrinho abandonado. Quando implementado, STC será atualizado para `85`, `86` ou `87` (= 70 + status anterior).

### 6.3 Cenário: Pedido Novo (Carrinho Não Existia no BD)

Quando o worker de pedidos encontra um `cart_id` que **não existe** na tabela:

1. **Cria nova linha** com `cart_id`, `order_id`, `data_pedido`, `data_carrinho`, `cpf`, `sku`.
2. `stg` = `NULL`, `stc` = `NULL`.
3. O worker de carrinhos **nunca** processará este registro (pois `order_id` já está preenchido desde a criação).

---

## 7. Worker de Pedidos — Contrato de Processamento

### 7.1 Fluxo de Entrada Atômico (para cada pedido no JSON)

O processamento deve ser estritamente **atômico e desmembrado em etapas de curtíssima duração de conexão**, impedindo que a sessão do banco fique presa durante operações de rede (como disparo de e-mails):

```
Fase 1: LEITURA E VINCULAÇÃO ATÔMICA (Lock de Milissegundos)
1. Requisitar acesso à conexão/lock da linha (cart_id).
2. Ao ganhar o lock:
   ├── Se cart_id existe: Vincular order_id, data_pedido, atualizar cpf, sku.
   └── Se cart_id não existe: Criar nova linha (stg=null, stc=null).
3. Ler o stg atual.
4. LIBERAR O LOCK E FECHAR A TRANSAÇÃO DO BANCO IMEDIATAMENTE.

Fase 2: PROCESSAMENTO E I/O EXTERNO (Sem Lock no Banco)
5. Se stg ∈ {1, 3, 8, 95, 96, 97} → SKIP (terminal, encerrar item).
6. Avaliar condições de transição temporais e de pagamento (seção 4.2).
7. Se houver envio de email: Executar disparo I/O (SMTP/Network) FORA do banco de dados.

Fase 3: GRAVAÇÃO ATÔMICA (Lock de Milissegundos)
8. Requisitar acesso à conexão/lock da linha (cart_id) novamente.
9. Ao ganhar o lock:
   └── Gravar novo stg e sobrescrever timestamp_ultimo_email.
10. LIBERAR O LOCK E FECHAR A TRANSAÇÃO IMEDIATAMENTE (disponível para outros workers).
```

### 7.2 Detecção de Recompra (Status 99) - future implementation

Executada **apenas** quando o pedido tem pagamento aprovado:

```
1. Buscar cpf na email_status_table (índice idx_email_status_cpf)
2. Se encontrou outro registro com mesmo cpf:
   ├── Buscar se algum registro com mesmo cpf E mesmo sku existe
   │   ├── SIM → É recompra. Marcar (future implementation).
   │   └── NÃO → Não é recompra do mesmo produto.
   └── NÃO → Cliente novo, sem histórico.
```

---

## 8. Worker de Carrinhos Abandonados — Contrato de Processamento

### 8.1 Fluxo de Entrada Atômico (para cada carrinho no JSON)

```
Fase 1: LEITURA ATÔMICA (Lock de Milissegundos)
1. Requisitar acesso à conexão/lock da linha (cart_id).
2. Ao ganhar o lock:
   ├── Se cart_id existe:
   │   ├── Se order_id IS NOT NULL → Liberar lock e SKIP (carrinho virou pedido).
   │   └── Se order_id IS NULL → Ler stc atual.
   └── Se cart_id não existe: Criar nova linha (cart_id, data_carrinho, cpf, sku, stc=null, order_id=null).
3. LIBERAR O LOCK E FECHAR A TRANSAÇÃO DO BANCO IMEDIATAMENTE.

Fase 2: PROCESSAMENTO E I/O EXTERNO (Sem Lock no Banco)
4. Se stc ∈ {18, 85, 86, 87} → SKIP (terminal).
5. Avaliar transição temporal (seção 5.3).
6. Se houver envio de email: Executar disparo I/O com link simulate_url FORA do banco.

Fase 3: GRAVAÇÃO ATÔMICA (Lock de Milissegundos)
7. Requisitar acesso à conexão/lock da linha (cart_id) novamente.
8. Ao ganhar o lock:
   └── Gravar novo stc e sobrescrever timestamp_ultimo_email.
9. LIBERAR O LOCK E FECHAR A TRANSAÇÃO IMEDIATAMENTE.
```

---

## 9. Concorrência e Locking Atômico de Alta Performance

### 9.1 Problema de Contenção e Deadlock

Se um worker mantiver uma transação SQL aberta (`BEGIN ... FOR UPDATE`) enquanto realiza operações lentas de rede (disparo de e-mail por SMTP, renderização HTML ou chamadas HTTP), outros workers (pedidos ou carrinhos) ficarão bloqueados aguardando a conexão ser liberada, travando o banco de dados e causando *starvation* ou *timeouts*.

### 9.2 Solução: Padrão "Adquire - Processa Fora - Grava Curtíssimo"

Para garantir concorrência fluida e sem travamentos entre os workers de Pedidos e Carrinhos:

1. **Locks Atômicos de Curta Duração**: Transações SQL devem durar apenas os poucos milissegundos necessários para executar a instrução `SELECT ... FOR UPDATE` ou `UPDATE`.
2. **Isolamento de I/O Externo**: **Nenhuma** chamada de rede, API externa ou envio de e-mail pode ser feito com uma transação SQL aberta.
3. **Fila de Re-Entrada**: Cada worker requisita o lock da linha, realiza a leitura/verificação inicial, libera a sessão imediatamente para outros workers, executa a regra de negócio/envio no código Python, e só então requisita novamente o lock para gravar a atualização final.

```sql
-- Fase 1: Leitura Rápida (Ganhou -> Lê -> Libera)
BEGIN;
SELECT order_id, stg, stc FROM email_status_table WHERE cart_id = %s FOR UPDATE;
COMMIT; -- Libera o lock imediatamente!

-- (Processamento Python & Envio de E-mail via SMTP ocorrem aqui, fora do banco)

-- Fase 3: Gravação Rápida (Ganhou -> Grava -> Libera)
BEGIN;
UPDATE email_status_table SET stg = %s, timestamp_ultimo_email = %s WHERE cart_id = %s;
COMMIT;
```

O `FOR UPDATE` garante que apenas um worker por vez modifica cada linha, evitando race conditions.

---

## 10. Inventário de Emails

| ID | Nome | Fluxo | Gatilho | Conteúdo Principal |
|---|---|---|---|---|
| Email 1 | Confirmação + Pagamento | STG null→1 | Pagamento aprovado de primeira | Confirmação da compra + aviso de rastreio futuro |
| Email 2 | Incentivo ao Pagamento | STG null→2 | Pedido ≤30 min, pagamento pendente | Confirmação do pedido + apelo + PIX/QR Code |
| Email 3 | Confirmação Tardia | STG 2→3 | Pagamento aprovado após Email 2 | Idêntico ao Email 1 |
| Cupom 1 | Cupom Pedido 10% | STG 4→5 | >12h desde pedido | Cupom 10% de desconto |
| Cupom 2 | Cupom Pedido 15% | STG 5→6 | >14h desde pedido | Cupom 15% de desconto |
| Cupom 3 | Cupom Pedido 20% | STG 6→7 | >16h desde pedido | Cupom 20% de desconto |
| Cupom 4 | Cupom Carrinho + Link | STC null→15 | >14h desde carrinho | Cupom + botão `simulate_url` |
| Cupom 5 | Cupom Carrinho + Link | STC 15→16 | >16h desde carrinho | Cupom + botão `simulate_url` |
| Cupom 6 | Cupom Carrinho + Link | STC 16→17 | >18h desde carrinho | Cupom + botão `simulate_url` |

---

## 11. Future Implementation & Future Updates (Pendências e Evoluções Futuras)

Nesta seção estão listados todos os detalhes técnicos, pendências de validação e recursos planejados para as próximas versões do sistema:

### 11.1 Validação de Parâmetros Pendentes na API Yampi
- **Confirmação de Status de Envio/Cancelamento**: Fazer chamada ao endpoint `GET /v2/{alias}/checkout/statuses` na conta de produção da Yampi para homologar os IDs exatos de:
  - `cancelled` (Pedido Cancelado) → a confirmar se `status_id = 6`.
  - `shipped` (Em transporte/Despachado) → a confirmar se `status_id = 7`.
  - `delivered` (Entregue) → a confirmar se `status_id = 9`.
  - `refunded` (Reembolsado) → a confirmar se `status_id = 12`.
- **Validação de Payload de Rastreamento (`shipments`)**: Coletar uma amostra de payload real de um pedido com status `shipped` para validar os campos exactos `tracking_code` e `tracking_url` dentro da estrutura `shipments.data[0]`.

### 11.2 Status 95, 96, 97 (Recompra via Pedido)
- **Fórmula**: `90 + STG anterior` (ex: se STG era 5 → vira 95).
- **Gatilho**: Detecção de recompra por um mesmo cliente (cruzamento O(1) de `cpf` + `sku`) em pedido com pagamento aprovado.
- **Ação**: Disparo do "E-mail de Recompra" (agradecendo ao cliente por retornar e comprar novamente).

### 11.3 Status 85, 86, 87 (Conversão de Carrinho Abandonado)
- **Fórmula**: `70 + STC anterior` (ex: se STC era 16 → vira 86).
- **Gatilho**: Identificação de que um carrinho abandonado foi convertido em pedido após o envio do cupom de recuperação.
- **Ação**: Disparo do "E-mail de Agradecimento por Conversão de Carrinho".

### 11.4 Algoritmo Autônomo de Varredura de Recompra
- Desenvolvimento de um worker autônomo específico que executa periodicamente analisando a `email_status_table`, cruzando `cpf`, `sku` e intervalo de datas entre compras para inferir hábitos de recompra e alimentar relatórios.

### 11.5 Evolução para Webhooks em Tempo Real
- Substituição/Complementação da consulta por polling (a cada 5 minutos) por um servidor de recepção de Webhooks da Yampi (`order.paid`, `order.status.updated`), permitindo disparo de e-mails instantâneo em milissegundos.

### 11.6 Purga e Arquivamento de Dados Históricos
- Criação de uma rotina de manutenção no banco PostgreSQL para mover registros de `email_status_table` com mais de 365 dias para uma tabela de histórico/archive, mantendo o índice ativo enxuto e de alta velocidade.

### 11.7 Gestão do Banco de Dados em Produção e Migrações DDL
- **Estudo da Criação de Tabelas (`_init_db`) e `ALTER TABLE` no Startup**:
  - *Comportamento Atual*: A aplicação executa instruções DDL (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`) dentro de `_init_db()` na inicialização do repositório Python.
  - *Evolução para Produção*:
    - Analisar a substituição das DDLs em tempo de execução por ferramentas especializadas de migração de banco de dados (ex: Alembic ou Flyway).
    - Em ambiente de alta disponibilidade com múltiplos nós rodando em paralelo, chamadas de DDL no startup do código podem gerar travamentos de catálogo (`AccessExclusiveLock`).
    - Estabelecer diretrizes estritas para que qualquer alteração de schema em produção (como adicionar colunas `NOT NULL`) utilize valores padrões (`DEFAULT 'N/A'`) ou rotinas de *backfill* isoladas antes da alteração rígida da tabela.


---

## 12. Diagramas de Referência

- **Índice Geral de Diagramas:** [README.md do Diretório de Diagramas](./diagramas/README.md)
- **Fluxo STG (Pedidos):** [stateDiagramOrders.md](./diagramas/stateDiagramOrders.md)
- **Fluxo STC (Carrinhos):** [stateDiagramAbandonedCarts.md](./diagramas/stateDiagramAbandonedCarts.md)

---

## 13. Mapeamento Técnico de Parâmetros da API Yampi (Contrato de Dados)

### 13.1 Módulo de Pedidos (`GET /v2/{alias}/orders?include=customer,items,shipments,status`)

Fonte dos dados: `estudos/yampi_api/pedidos.json`

| Parâmetro da Arquitetura | Caminho Exato no JSON da Yampi | Tipo | Exemplo Coletado / Status |
|---|---|---|---|
| **ID do Pedido** (`order_id`) | `order['id']` | `int` | `167930539` (Confirmado ✓) |
| **ID do Carrinho de Origem** (`cart_id`) | `order['metadata']['data']` (item com `key == "cart_id"`) | `string` | `"626595483"` (Confirmado ✓) |
| **Data de Criação do Pedido** (`data_pedido`) | `order['created_at']['date']` | `string` | `"2026-07-20 18:42:18.000000"` (Confirmado ✓) |
| **ID Numérico do Status** | `order['status']['data']['id']` | `int` | `3` ou `4` (Confirmado ✓) |
| **Alias Textual do Status** | `order['status']['data']['alias']` | `string` | `"waiting_payment"`, `"paid"` (Confirmado ✓) |
| **Nome Legível do Status** | `order['status']['data']['name']` | `string` | `"Aguardando pagamento"`, `"Pagamento aprovado"` (Confirmado ✓) |
| **CPF do Cliente** | `order['customer']['data']['cpf']` | `string` | `"74327836915"` (Confirmado ✓) |
| **Nome do Cliente** | `order['customer']['data']['name']` | `string` | `"Clau Cimardi"` (Confirmado ✓) |
| **E-mail do Cliente** | `order['customer']['data']['email']` | `string` | `"claucimardi11@gmail.com"` (Confirmado ✓) |
| **Array de Itens** | `order['items']['data']` | `array` | Lista de produtos (Confirmado ✓) |
| **SKU do Produto** | `item['item_sku']` ou `item['sku']['data']['sku']` | `string` | `"BUBBLE-3.5CM"` (Confirmado ✓) |
| **Preço do Produto** | `item['price']` | `float` | `105.90` (usado para filtro do SKU mais caro) |
| **Código de Rastreio** | `order['shipments']['data'][0]['tracking_code']` | `string` | `"BR123456789BR"` (Nota: a chave `data` pode ser dict ou array polimórfico dependendo do payload. Fallbacks aplicados no `base_builder.py`) |
| **URL de Rastreio** | `order['shipments']['data'][0]['tracking_url']` | `string` | Link dos Correios (Fallback: `"#"`) |



### 13.2 Módulo de Carrinhos Abandonados (`GET /v2/{alias}/checkout/carts?include=customer,items`)

Fonte dos dados: `estudos/yampi_api/carrinhos.json`

| Parâmetro da Arquitetura | Caminho Exato no JSON da Yampi | Tipo | Exemplo Coletado / Status |
|---|---|---|---|
| **ID do Carrinho** (`cart_id`) | `cart['id']` | `int` → `string` | `626597705` (Confirmado ✓) |
| **Token do Carrinho** | `cart['token']` | `string` | `"hWNEi8eWf0KLTgX6JNA192Xq"` (Confirmado ✓) |
| **Data de Criação** (`data_carrinho`) | `cart['created_at']['date']` | `string` | `"2026-07-20 18:49:18.000000"` (Confirmado ✓) |
| **Link de Recuperação** | `cart['simulate_url']` | `string` | URL com token do checkout (Confirmado ✓) |
| **CPF do Cliente** | `cart['customer']['data']['cpf']` | `string` | `"81612184391"` (Confirmado ✓) |
| **Nome do Cliente** | `cart['customer']['data']['name']` | `string` | `"Davi Pessoa Carneiro"` (Confirmado ✓) |
| **E-mail do Cliente** | `cart['customer']['data']['email']` | `string` | `"davipessoacarneiro@gmail.com"` (Confirmado ✓) |
| **Link WhatsApp** | `cart['customer']['data']['phone']['whatsapp_link']` | `string` | Link direto para WhatsApp (Confirmado ✓) |
| **Array de Itens** | `cart['items']['data']` | `array` | Produtos esquecidos (Confirmado ✓) |

### 13.3 Mapeamento de Status da Yampi (STG / Pedidos)

Conforme verificado em `estudos/yampi_api/pedidos.json` e documentação oficial da Yampi:

| `status_id` | `alias` | `name` | Mapeamento Lógico STG | Status de Confirmação |
|---|---|---|---|---|
| `3` | `"waiting_payment"` | `"Aguardando pagamento"` | Transiciona para STG `2` (se `diff ≤ 30min`) ou STG `4` (se `diff > 30min`) | **Confirmado ✓** (via `pedidos.json`) |
| `4` | `"paid"` | `"Pagamento aprovado"` | Transiciona para STG `1` (se de primeira) ou STG `3` (se após incentivo) | **Confirmado ✓** (via `pedidos.json`) |
| `6` | `"cancelled"` | `"Cancelado"` | Ignorado no precheck, permitindo que a regra temporal do STG 4 e subsequentes trate o pedido como não aprovado, guiando o cliente para re-compra. | **Confirmado ✓** (via nova regra de pipeline) |
| `7` | `"shipped"` | `"Em transporte"` | Dispara E-mail de Rastreio | **A Confirmar** (a validar em endpoint `/checkout/statuses`) |
| `9` | `"delivered"` | `"Entregue"` | Pedido finalizado com sucesso | **A Confirmar** (a validar em endpoint `/checkout/statuses`) |
| `12` | `"refunded"` | `"Reembolsado"` | Pedido reembolsado | **A Confirmar** (a validar em endpoint `/checkout/statuses`) |


