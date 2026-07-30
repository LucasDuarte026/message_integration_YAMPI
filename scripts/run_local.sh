#!/bin/bash

# Diretório raiz do projeto (um nível acima)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Exporta variáveis do .env na raiz
set -a
source "$PROJECT_ROOT/.env"
set +a

# Executa o main.py com os argumentos passados
"$PROJECT_ROOT/.venv/bin/python3" "$PROJECT_ROOT/src/main.py" "$@"
