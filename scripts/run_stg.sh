#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

set -a
source "$PROJECT_ROOT/.env"
set +a

# Executa o Worker de Pedidos (STG - Status Global)
"$PROJECT_ROOT/.venv/bin/python3" "$PROJECT_ROOT/src/main.py" orders "$@"
