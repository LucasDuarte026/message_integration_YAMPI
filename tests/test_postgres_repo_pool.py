import pytest
from unittest.mock import patch, MagicMock
from src.ports.postgres_repo import PostgresStateRepository
import concurrent.futures
from datetime import datetime
import psycopg2.extras

@patch("src.ports.postgres_repo.ThreadedConnectionPool")
def test_postgres_repo_connection_pool_concurrency(mock_pool_class):
    # Setup the mock pool
    mock_pool_instance = MagicMock()
    mock_pool_class.return_value = mock_pool_instance
    
    # Setup mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # getconn() should return our mock connection
    mock_pool_instance.getconn.return_value = mock_conn
    
    # cursor() context manager (with conn.cursor() as cur:)
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    # __exit__ should return False to not suppress exceptions
    mock_conn.__exit__.return_value = False
    mock_conn.cursor.return_value.__exit__.return_value = False
    
    # Initialize repository
    repo = PostgresStateRepository("fake_db_url")
    
    # Ensure pool was created correctly
    mock_pool_class.assert_called_once()
    assert mock_pool_class.call_args[0] == (1, 20, "fake_db_url")
    
    # Define a function to run concurrently
    def worker_task(cart_id):
        repo.upsert_from_cart(
            cart_id=str(cart_id),
            data_carrinho=datetime.now(),
            cpf="12345678901",
            sku="SKU-TEST"
        )
        return True

    # Simulate 10 workers hitting the repository at the same time
    num_workers = 10
    num_tasks = 50
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker_task, i) for i in range(num_tasks)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
    assert all(results)
    assert len(results) == num_tasks
    
    # Assert getconn and putconn were called num_tasks times + 1 time for _init_db
    expected_calls = num_tasks + 1
    assert mock_pool_instance.getconn.call_count == expected_calls
    assert mock_pool_instance.putconn.call_count == expected_calls
    
    # Assert cursor executed queries
    assert mock_cursor.execute.call_count >= num_tasks
    
    # Test close method
    repo.close()
    mock_pool_instance.closeall.assert_called_once()


def _criar_repo_com_pool_mock(mock_pool_class):
    """Cria um PostgresStateRepository com pool, conexão e cursor mockados."""
    mock_pool_instance = MagicMock()
    mock_pool_class.return_value = mock_pool_instance

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_pool_instance.getconn.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = False

    repo = PostgresStateRepository("fake_db_url")
    mock_cursor.execute.reset_mock()
    return repo, mock_pool_instance, mock_conn, mock_cursor


@patch("src.ports.postgres_repo.ThreadedConnectionPool")
def test_upsert_from_order_uses_coalesce_least_and_returns_row(mock_pool_class):
    """Verifica se upsert_from_order protege data_pedido com COALESCE(LEAST(...)) e retorna a linha."""
    repo, _, mock_conn, mock_cursor = _criar_repo_com_pool_mock(mock_pool_class)
    expected_row = {"cart_id": "c-1", "order_id": "o-1", "stg": 2}
    mock_cursor.fetchone.return_value = expected_row

    result = repo.upsert_from_order(
        cart_id="c-1",
        order_id="o-1",
        order_number="1001",
        data_pedido=datetime(2026, 8, 10, 12, 0, 0),
        cpf=None,
        sku=None,
    )

    assert result == expected_row
    upsert_sql, upsert_params = mock_cursor.execute.call_args_list[0][0]
    assert "COALESCE(LEAST(email_status_table.data_pedido, EXCLUDED.data_pedido), EXCLUDED.data_pedido)" in upsert_sql
    assert upsert_params[0] == "c-1"
    assert upsert_params[2] == "1001"
    mock_conn.commit.assert_called()


@patch("src.ports.postgres_repo.ThreadedConnectionPool")
def test_update_stg_and_update_stc_execute_queries(mock_pool_class):
    """Verifica se update_stg e update_stc atualizam status e timestamp_ultimo_email em UTC."""
    repo, _, mock_conn, mock_cursor = _criar_repo_com_pool_mock(mock_pool_class)

    repo.update_stg("c-1", 3)
    stg_sql, stg_params = mock_cursor.execute.call_args_list[0][0]
    assert "SET stg = %s, timestamp_ultimo_email = %s" in stg_sql
    assert stg_params[0] == 3
    assert stg_params[2] == "c-1"

    mock_cursor.execute.reset_mock()
    repo.update_stc("c-2", 16)
    stc_sql, stc_params = mock_cursor.execute.call_args_list[0][0]
    assert "SET stc = %s, timestamp_ultimo_email = %s" in stc_sql
    assert stc_params[0] == 16
    assert stc_params[2] == "c-2"
    assert mock_conn.commit.call_count >= 2


@patch("src.ports.postgres_repo.ThreadedConnectionPool")
def test_postgres_repo_exception_handling(mock_pool_class):
    """Verifica tratamento de falhas SQL nos métodos do repositório e propagação em _init_db."""
    repo, mock_pool_instance, _, mock_cursor = _criar_repo_com_pool_mock(mock_pool_class)
    mock_cursor.execute.side_effect = RuntimeError("Erro simulado no Postgres")

    assert repo.upsert_from_order("c-1", "o-1", None, datetime.now(), None, None) is None
    assert repo.upsert_from_cart("c-1", datetime.now(), None, None) is None

    # update_stg e update_stc não devem propagar exceções
    repo.update_stg("c-1", 4)
    repo.update_stc("c-1", 15)

    # putconn deve ser chamado mesmo quando ocorre exceção
    assert mock_pool_instance.putconn.call_count == 5

    # _init_db deve propagar erro na inicialização
    mock_pool_class.return_value = mock_pool_instance
    with pytest.raises(RuntimeError, match="Erro simulado no Postgres"):
        PostgresStateRepository("fake_db_url")
