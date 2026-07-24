#!/bin/bash

# Exporta todas as variáveis do .env
set -a
source .env
set +a

# Executa o main.py passando qualquer argumento extra (ex: all, orders, abandoned-carts)
# Se você quiser rodar em produção enviando emails reais, pode usar: ./run_local.sh all --production
.venv/bin/python3 src/main.py "$@"
