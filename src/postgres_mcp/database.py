import logging
import psycopg
from psycopg.rows import dict_row
from .config import database_url
from .operations.sales import QUERIES

log = logging.getLogger('postgres-mcp')


def execute(operation: str, params: tuple):
    # Lookup occurs before connecting: unknown operations cannot reach the DB.
    query = QUERIES[operation]
    dsn = database_url()
    try:
        with psycopg.connect(dsn, connect_timeout=3, row_factory=dict_row) as conn:
            with conn.transaction():
                conn.execute('SET TRANSACTION READ ONLY')
                conn.execute("SET LOCAL statement_timeout = '2s'")
                rows = conn.execute(query, params).fetchall()
        log.info('operation=%s status=ok rows=%d', operation, len(rows))
        return rows
    except psycopg.Error:
        log.warning('operation=%s status=failed', operation)
        raise ValueError('Данные временно недоступны') from None
