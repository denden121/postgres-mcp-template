from unittest.mock import patch
import pytest
from postgres_mcp import database


def test_unknown_operation_never_connects():
    with patch.object(database.psycopg, 'connect') as connect:
        with pytest.raises(KeyError):
            database.execute('execute_sql', ('DROP TABLE private.orders',))
        connect.assert_not_called()


def test_database_errors_do_not_leak_details():
    with patch.object(database, 'database_url', return_value='unused'), patch.object(
        database.psycopg, 'connect', side_effect=database.psycopg.OperationalError('secret password')
    ):
        with pytest.raises(ValueError, match='Данные временно недоступны') as error:
            database.execute('sales_summary', ())
        assert 'secret' not in str(error.value)
