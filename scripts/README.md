# Scripts de Consulta e Execução de Banco de Dados (`scripts`)

> [!IMPORTANT]
> **Aviso de Arquitetura**: Esta pasta contém os scripts base, porém o ponto de entrada principal (Facade) para orquestração e execução de todos os comandos do projeto é o **`Makefile`** na raiz do repositório. Sempre prefira utilizar os comandos via `make` (ex: `make run-orders`, `make db-query`).

Este diretório contém os scripts utilitários Shell e Python para execução de workers e consultas de status no banco de dados PostgreSQL (`email_status_table`) por **STG (Status Global / Pedidos)** e **STC (Status Carrinho / Carrinhos Abandonados)**.

---

## 📂 Arquivos no Diretório

| Script | Tipo | Descrição | Equivalente Make |
| :--- | :--- | :--- | :--- |
| 📦 **`run_stg.sh`** | Bash | Executa o Worker de Pedidos (**STG**). | `make run-orders` |
| 🛒 **`run_stc.sh`** | Bash | Executa o Worker de Carrinhos Abandonados (**STC**). | `make run-carts` |
| 🚀 **`run_local.sh`** | Bash | Executa o orquestrador principal (`main.py`). | `make run-all` |
| 🔍 **`search_stg.sh`** | Bash | Busca no banco por estado **STG**. | `make db-search-orders` |
| 🔍 **`search_stc.sh`** | Bash | Busca no banco por estado **STC**. | `make db-search-carts` |
| 🔎 **`find_by_id.sh`** | Bash | Busca rápida por registro no banco via ID. | `make db-find` |
| 🐳 **`query_all.sh`** | Bash | Executa consulta SQL direta no container Docker. | `make db-query` |
| 🗑️ **`delete_by_id.sh`** | Bash | Exclui um registro do banco via ID. | `make db-del` |
| 🐍 **`search_status.py`** | Python | Utilitário interno para consultas em `email_status_table`. | - |
| 🛡️ **`security_audit.sh`** | Bash | Orquestrador DevSecOps (TruffleHog, Semgrep, Trivy e SkillSpector). | `make security-audit` |

---

## 💻 Exemplos de Uso

### 1. Consultar Banco de Dados via Docker Compose (SQL Direto ou Busca por ID)
```bash
# Buscar por um ID específico (cart_id, order_id ou order_number)
./scripts/find_by_id.sh 168181758

# Executar a consulta completa via script
./scripts/query_all.sh

# Ou rodar o comando Docker direto no terminal:
docker compose exec -it db psql -U "$DB_USER" -d "$DB_NAME" -c 'SELECT * FROM email_status_table;'
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
*(Nota: o modo de disparo real SMTP vs Dry-Run é governado por `MACRO_ENABLE_REAL_EMAIL_DISPATCH` em `src/core/macros.py`, atualmente `True`. Não há flag `--production` via CLI.)*

```bash
# Processar Pedidos (STG)
./scripts/run_stg.sh

# Processar Carrinhos (STC)
./scripts/run_stc.sh

# Processar ambos (STG + STC)
./scripts/run_local.sh all
```

---

### 4. Auditoria de Segurança DevSecOps (`security_audit.sh`)

```bash
# Executar bateria completa (TruffleHog + Semgrep + Trivy + SkillSpector)
make security-audit

# Executar verificação rápida pré-commit/pré-push (Segredos + SAST + Skills)
make security-quick

# Executar camadas individuais
make security-secrets  # TruffleHog (histórico Git e arquivos)
make security-sast     # Semgrep (análise estática Python/Flask/SQL)
make security-infra    # Trivy (requirements.txt, Dockerfile e Docker Compose)
make security-skills   # SkillSpector (auditoria de skills em .agents/skills/)
```
