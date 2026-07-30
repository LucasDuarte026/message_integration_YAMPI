#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

set -a
source "$PROJECT_ROOT/.env"
set +a

# Busca registros por STC no banco de dados (ou executa o worker de Carrinhos se usar --run)
if [ "$1" == "--run" ]; then
    shift
    "$PROJECT_ROOT/.venv/bin/python3" "$PROJECT_ROOT/src/main.py" abandoned-carts "$@"
else
    "$PROJECT_ROOT/.venv/bin/python3" "$SCRIPT_DIR/search_status.py" --stc "$@"
fi
