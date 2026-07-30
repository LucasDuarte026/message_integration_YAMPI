# Scripts de Consulta e Execução de Banco de Dados (`scripts`)

Este diretório contém os scripts utilitários Shell e Python para execução de workers e consultas de status no banco de dados PostgreSQL (`email_status_table`) por **STG (Status Global / Pedidos)** e **STC (Status Carrinho / Carrinhos Abandonados)**.

---

## 📂 Arquivos no Diretório

| Script | Tipo | Descrição |
| :--- | :--- | :--- |
| 📦 **`run_stg.sh`** | Bash | Executa o Worker de Pedidos (**STG**). |
| 🛒 **`run_stc.sh`** | Bash | Executa o Worker de Carrinhos Abandonados (**STC**). |
| 🚀 **`run_local.sh`** | Bash | Executa o orquestrador principal (`main.py`) aceitando qualquer parâmetro (`all`, `orders`, `abandoned-carts`). |
| 🔍 **`search_stg.sh`** | Bash | Realiza consultas no banco por estado **STG** (ex: `./search_stg.sh 2`). |
| 🔍 **`search_stc.sh`** | Bash | Realiza consultas no banco por estado **STC** (ex: `./search_stc.sh 15`). |
| 🔎 **`find_by_id.sh`** | Bash | Busca rápida por registro no banco via `order_id`, `cart_id` ou `order_number`. |
| 🐳 **`query_all.sh`** | Bash | Executa consulta SQL direta no container Docker Postgres (`SELECT * from email_status_table`). |
| 🐍 **`search_status.py`** | Python | Utilitário interno consumido pelos scripts de busca para consultar `email_status_table`. |

---

## 💻 Exemplos de Uso

### 1. Consultar Banco de Dados via Docker Compose (SQL Direto ou Busca por ID)
```bash
# Buscar por um ID específico (cart_id, order_id ou order_number)
./scripts/find_by_id.sh 168181758

# Executar a consulta completa via script
./scripts/query_all.sh

# Ou rodar o comando Docker direto no terminal:
docker compose exec -it db psql -U lucas -d magal_database -c 'SELECT * from email_status_table'
```

### 2. Consultar Banco de Dados por Status (Python)
```bash
# Listar todos os registros com STG preenchido
./scripts/search_stg.sh

# Listar registros com STG = 2 (Incentivo PIX Pendente)
./scripts/search_stg.sh 2

# Listar todos os registros com STC preenchido
./scripts/search_stc.sh

# Listar registros com STC = 15 (Cupom 4 enviado)
./scripts/search_stc.sh 15
```

### 3. Executar Workers Diretos
```bash
# Processar Pedidos (STG) em modo Dry-Run
./scripts/run_stg.sh

# Processar Pedidos (STG) em Produção (envio real via SMTP)
./scripts/run_stg.sh --production

# Processar Carrinhos (STC) em modo Dry-Run
./scripts/run_stc.sh
```
