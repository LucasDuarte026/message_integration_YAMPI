#!/usr/bin/env bash

# ==============================================================================
# Script de busca rápida no Banco de Dados por ID (order_id, cart_id ou order_number)
# Uso: ./scripts/find_by_id.sh <ID>
# Exemplo: ./scripts/find_by_id.sh 168181758
# Exemplo: ./scripts/find_by_id.sh 627315620
# ==============================================================================

if [ -z "$1" ]; then
  echo "Uso: $0 <ID_PEDIDO_OU_CART_ID>"
  echo "Exemplo: $0 168181758"
  exit 1
fi

SEARCH_ID="$1"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

if [ -f "$PROJECT_ROOT/.env" ]; then
  set -a
  source "$PROJECT_ROOT/.env"
  set +a
fi

# Tenta ler as credenciais do .env caso existam, ou usa o padrão
DB_USER=${DB_USER:-lucas}
DB_NAME=${DB_NAME:-magal_database}
CONTAINER_NAME="message_integration_db"

echo "🔎 Buscando ID: '${SEARCH_ID}' no banco PostgreSQL (${CONTAINER_NAME})..."
echo "=============================================================================="

docker exec ${CONTAINER_NAME} psql -U "${DB_USER}" -d "${DB_NAME}" \
  -c "\x on" \
  -c "SELECT * FROM email_status_table WHERE cart_id = '${SEARCH_ID}' OR order_id = '${SEARCH_ID}' OR order_number = '${SEARCH_ID}';"
