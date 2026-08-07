#!/usr/bin/env bash

# ==============================================================================
# Script interativo de exclusão no Banco de Dados por campo e valor
# Uso: ./scripts/delete_by_id.sh <CAMPO> <VALOR>
#   ou ./scripts/delete_by_id.sh <VALOR_ID>
# Exemplo: ./scripts/delete_by_id.sh order_id 168181758
# Exemplo: ./scripts/delete_by_id.sh 168181758
# ==============================================================================

if [ -z "$1" ]; then
  echo "Uso: $0 <CAMPO> <VALOR>"
  echo "  ou: $0 <ID>"
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

DB_USER=${DB_USER:-lucas}
DB_NAME=${DB_NAME:-magal_database}
CONTAINER_NAME="message_integration_db"

if [ -n "$2" ]; then
  FIELD="$1"
  VALUE="$2"

  if [[ ! "$FIELD" =~ ^[a-zA-Z0-9_]+$ ]]; then
    echo "❌ Nome do campo inválido: '$FIELD'"
    exit 1
  fi

  WHERE_CLAUSE="${FIELD}::text = '${VALUE}'"
  SEARCH_DESC="'${FIELD}' = '${VALUE}'"
else
  SEARCH_ID="$1"
  WHERE_CLAUSE="cart_id::text = '${SEARCH_ID}' OR order_id::text = '${SEARCH_ID}' OR order_number::text = '${SEARCH_ID}'"
  SEARCH_DESC="ID '${SEARCH_ID}' (cart_id / order_id / order_number)"
fi

echo "🔎 Buscando registros por ${SEARCH_DESC} no banco PostgreSQL (${CONTAINER_NAME})..."
echo "=============================================================================="

# Busca registros formatados em tabela
RECORDS=$(docker exec ${CONTAINER_NAME} psql -U "${DB_USER}" -d "${DB_NAME}" \
  -t -A -F" | " \
  -c "SELECT cart_id, COALESCE(order_id, 'NULL'), COALESCE(order_number, 'N/A'), COALESCE(cpf, 'N/A'), COALESCE(sku, 'N/A'), COALESCE(stg::text, 'NULL'), COALESCE(stc::text, 'NULL') FROM email_status_table WHERE ${WHERE_CLAUSE};")

if [ -z "$RECORDS" ]; then
  echo "⚠️ Nenhum registro encontrado para ${SEARCH_DESC}."
  exit 0
fi

# Converte o resultado em um array
mapfile -t RECORD_LIST <<< "$RECORDS"
TOTAL_FOUND=${#RECORD_LIST[@]}

echo "📌 Encontrado(s) ${TOTAL_FOUND} registro(s):"
echo "------------------------------------------------------------------------------"
printf "%-3s | %-20s | %-20s | %-15s | %-15s | %-4s | %-4s\n" "Nº" "CART_ID" "ORDER_ID" "ORDER_NUMBER" "SKU" "STG" "STC"
echo "------------------------------------------------------------------------------"

i=1
declare -A CART_MAP
for row in "${RECORD_LIST[@]}"; do
  IFS=" | " read -r cart_id order_id order_number cpf sku stg stc <<< "$row"
  CART_MAP[$i]="$cart_id"
  printf "%-3d | %-20s | %-20s | %-15s | %-15s | %-4s | %-4s\n" "$i" "$cart_id" "$order_id" "$order_number" "$sku" "$stg" "$stc"
  ((i++))
done
echo "------------------------------------------------------------------------------"

echo ""
if [ "$TOTAL_FOUND" -eq 1 ]; then
  TARGET_CART_ID="${CART_MAP[1]}"
  echo "❓ É este mesmo o registro que você deseja excluir? (cart_id: ${TARGET_CART_ID})"
  read -p "Confirma a exclusão permanente? (s/N): " CONFIRM
  if [[ "$CONFIRM" =~ ^[sS]$ ]]; then
    DELETE_QUERY="DELETE FROM email_status_table WHERE cart_id = '${TARGET_CART_ID}';"
  else
    echo "❌ Operação cancelada pelo usuário."
    exit 0
  fi
else
  echo "❓ Escolha uma opção:"
  echo "  [1-${TOTAL_FOUND}] Digite o número do registro específico para apagar"
  echo "  [A] Apagar TODOS os ${TOTAL_FOUND} registros listados acima"
  echo "  [C] Cancelar"
  read -p "Opção: " CHOICE

  if [[ "$CHOICE" =~ ^[cC]$ ]] || [ -z "$CHOICE" ]; then
    echo "❌ Operação cancelada."
    exit 0
  elif [[ "$CHOICE" =~ ^[aA]$ ]]; then
    read -p "⚠️ TEM CERTEZA que deseja apagar TODOS os ${TOTAL_FOUND} registros acima? (s/N): " CONFIRM
    if [[ "$CONFIRM" =~ ^[sS]$ ]]; then
      DELETE_QUERY="DELETE FROM email_status_table WHERE ${WHERE_CLAUSE};"
    else
      echo "❌ Operação cancelada pelo usuário."
      exit 0
    fi
  elif [[ "$CHOICE" =~ ^[0-9]+$ ]] && [ "$CHOICE" -ge 1 ] && [ "$CHOICE" -le "$TOTAL_FOUND" ]; then
    TARGET_CART_ID="${CART_MAP[$CHOICE]}"
    echo "🎯 Selecionado: cart_id=${TARGET_CART_ID}"
    read -p "Confirma a exclusão permanente deste registro? (s/N): " CONFIRM
    if [[ "$CONFIRM" =~ ^[sS]$ ]]; then
      DELETE_QUERY="DELETE FROM email_status_table WHERE cart_id = '${TARGET_CART_ID}';"
    else
      echo "❌ Operação cancelada pelo usuário."
      exit 0
    fi
  else
    echo "❌ Opção inválida."
    exit 1
  fi
fi

# Executa o DELETE no banco de dados
echo "🗑️ Executando exclusão no PostgreSQL..."
docker exec ${CONTAINER_NAME} psql -U "${DB_USER}" -d "${DB_NAME}" -c "${DELETE_QUERY}"

if [ $? -eq 0 ]; then
  echo "✅ Registro(s) excluído(s) com sucesso!"
else
  echo "❌ Falha ao excluir o registro."
fi
