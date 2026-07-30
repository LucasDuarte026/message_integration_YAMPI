import sys
import os
import argparse

# Adiciona a raiz do projeto ao path do Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.core.config import load_config

def search_database(mode: str, value: str = None):
    config = load_config()
    db_url = config.DATABASE_URL
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados PostgreSQL ({db_url}): {e}")
        sys.exit(1)
    
    if mode == "stg":
        if value is not None and value.lower() != "all":
            query = "SELECT cart_id, order_id, order_number, stg, stc, cpf, sku, data_pedido, timestamp_ultimo_email FROM email_status_table WHERE stg = %s ORDER BY data_pedido DESC NULLS LAST LIMIT 100;"
            cur.execute(query, (int(value),))
        else:
            query = "SELECT cart_id, order_id, order_number, stg, stc, cpf, sku, data_pedido, timestamp_ultimo_email FROM email_status_table WHERE stg IS NOT NULL ORDER BY data_pedido DESC NULLS LAST LIMIT 100;"
            cur.execute(query)
    elif mode == "stc":
        if value is not None and value.lower() != "all":
            query = "SELECT cart_id, order_id, order_number, stg, stc, cpf, sku, data_carrinho, timestamp_ultimo_email FROM email_status_table WHERE stc = %s ORDER BY data_carrinho DESC NULLS LAST LIMIT 100;"
            cur.execute(query, (int(value),))
        else:
            query = "SELECT cart_id, order_id, order_number, stg, stc, cpf, sku, data_carrinho, timestamp_ultimo_email FROM email_status_table WHERE stc IS NOT NULL ORDER BY data_carrinho DESC NULLS LAST LIMIT 100;"
            cur.execute(query)
            
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    val_str = f" = {value}" if value and value.lower() != "all" else " (Todos não nulos)"
    print(f"\n=======================================================")
    print(f"=== BUSCA NO BANCO DE DADOS: {mode.upper()}{val_str} ===")
    print(f"=======================================================")
    if not rows:
        print("Nenhum registro encontrado para o filtro informado.")
        return
        
    print(f"Total de registros encontrados: {len(rows)} (limite exibido: 100)\n")
    print(f"{'Cart ID':<15} | {'Order ID':<15} | {'Order #':<12} | {'STG':<5} | {'STC':<5} | {'CPF':<14} | {'SKU':<18}")
    print("-" * 95)
    for r in rows:
        cart_id = str(r['cart_id'] or 'N/A')
        order_id = str(r['order_id'] or 'N/A')
        order_num = str(r['order_number'] or 'N/A')
        stg = str(r['stg']) if r['stg'] is not None else 'NULL'
        stc = str(r['stc']) if r['stc'] is not None else 'NULL'
        cpf = str(r['cpf'] or 'N/A')
        sku = str(r['sku'] or 'N/A')
        print(f"{cart_id:<15} | {order_id:<15} | {order_num:<12} | {stg:<5} | {stc:<5} | {cpf:<14} | {sku:<18}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Busca de registros por STG ou STC no banco de dados.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stg", nargs="?", const="all", help="Buscar por STG (ex: 2 para STG=2 ou sem argumento para todos)")
    group.add_argument("--stc", nargs="?", const="all", help="Buscar por STC (ex: 15 para STC=15 ou sem argumento para todos)")
    
    args = parser.parse_args()
    if args.stg is not None:
        search_database("stg", args.stg)
    elif args.stc is not None:
        search_database("stc", args.stc)
