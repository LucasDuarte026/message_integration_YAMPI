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
