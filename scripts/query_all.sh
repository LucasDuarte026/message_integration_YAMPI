#!/bin/bash

# Executa consulta SQL direta no container do PostgreSQL via Docker Compose
docker compose exec -it db psql -U "${DB_USER:-lucas}" -d "${DB_NAME:-magal_database}" -c "${1:-SELECT * from email_status_table;}"