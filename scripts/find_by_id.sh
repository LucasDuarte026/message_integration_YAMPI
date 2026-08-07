#!/usr/bin/env bash

# ==============================================================================
# Script de busca rápida no Banco de Dados por campo e valor
# Uso: ./scripts/find_by_id.sh <CAMPO> <VALOR>
#   ou ./scripts/find_by_id.sh <VALOR_ID>
# Exemplo: ./scripts/find_by_id.sh sku 112254541
# Exemplo: ./scripts/find_by_id.sh order_id 168181758
# Exemplo (busca ID padrão): ./scripts/find_by_id.sh 168181758
# ==============================================================================

if [ -z "$1" ]; then
  echo "Uso: $0 <CAMPO> <VALOR>"
  echo "  ou: $0 <ID>"
  echo "Exemplo: $0 sku 112254541"
  echo "Exemplo: $0 order_id 168181758"
  echo "Exemplo: $0 168181758"
  exit 1
fi

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

if [ -n "$2" ]; then
  FIELD="$1"
  VALUE="$2"

  # Valida o nome do campo para garantir caracteres alfanuméricos/underscore
  if [[ ! "$FIELD" =~ ^[a-zA-Z0-9_]+$ ]]; then
    echo "❌ Nome do campo inválido: '$FIELD'"
    exit 1
  fi

  echo "🔎 Buscando por '${FIELD}' = '${VALUE}' no banco PostgreSQL (${CONTAINER_NAME})..."
  echo "=============================================================================="

  docker exec ${CONTAINER_NAME} psql -U "${DB_USER}" -d "${DB_NAME}" \
    -c "\x on" \
    -c "SELECT * FROM email_status_table WHERE ${FIELD}::text = '${VALUE}';"
else
  SEARCH_ID="$1"

  echo "🔎 Buscando ID: '${SEARCH_ID}' (cart_id / order_id / order_number) no banco PostgreSQL (${CONTAINER_NAME})..."
  echo "=============================================================================="

  docker exec ${CONTAINER_NAME} psql -U "${DB_USER}" -d "${DB_NAME}" \
    -c "\x on" \
    -c "SELECT * FROM email_status_table WHERE cart_id::text = '${SEARCH_ID}' OR order_id::text = '${SEARCH_ID}' OR order_number::text = '${SEARCH_ID}';"
fi

