from datetime import date
from unittest.mock import patch
import os
import pytest
import server

D = date(2026, 10, 1)

async def test_only_two_tools():
    assert {t.name for t in await server.mcp.list_tools()} == {"sales_summary", "top_products"}

@pytest.mark.parametrize('args', [
    {"start": "2026-10-01'; DROP TABLE sales;--", "end": "2026-10-31"},
    {"start": "2026-10-01", "end": "2026-10-31", "limit": 11},
    {"start": "2026-10-01", "end": "2026-10-31", "limit": True},
    {"start": "2026-10-31", "end": "2026-10-01"},
    {"start": "2026-01-01", "end": "2026-10-01"},
])
async def test_bad_inputs_never_reach_db(args):
    with patch.object(server, 'execute') as execute:
        with pytest.raises(Exception):
            await server.mcp.call_tool('top_products', args)
        execute.assert_not_called()

async def test_unknown_tool():
    with patch.object(server, 'execute') as execute:
        with pytest.raises(Exception):
            await server.mcp.call_tool('execute_sql', {'sql': 'DROP TABLE private.orders'})
        execute.assert_not_called()

def test_fixed_operation():
    with patch.object(server, 'execute', return_value=[]) as execute:
        server.top_products(D, D, 3)
        execute.assert_called_once_with('top_products', (D, D, 3))

@pytest.mark.skipif(not os.getenv('DATABASE_URL'), reason='Requires demo PostgreSQL')
def test_database_permissions():
    import psycopg
    with psycopg.connect(os.environ['DATABASE_URL'], autocommit=True) as conn:
        assert conn.execute("SELECT * FROM api.sales_summary('2026-10-01','2026-10-31')").fetchone() == (4, 5500)
        assert len(conn.execute("SELECT * FROM api.top_products('2026-10-01','2026-10-31',2)").fetchall()) == 2
        # Disable read-only default to demonstrate actual ACL protection.
        conn.execute('SET default_transaction_read_only = off')
        for sql in ['SELECT * FROM private.orders', 'DELETE FROM private.orders',
                    'DROP TABLE private.orders', 'CREATE TABLE public.hack(id int)',
                    'CREATE TEMP TABLE hack(id int)', 'SET ROLE data_owner']:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                conn.execute(sql)
        with pytest.raises(psycopg.Error):
            conn.execute("SELECT * FROM api.top_products('2026-10-01','2026-10-31',100)")

@pytest.mark.skipif(not os.getenv('DATABASE_URL'), reason='Requires demo PostgreSQL')
async def test_stdio_end_to_end():
    import sys
    from pathlib import Path
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(server.__file__).resolve())],
        env={**os.environ},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            tools = await client.list_tools()
            assert {t.name for t in tools.tools} == {'sales_summary', 'top_products'}
            summary = await client.call_tool('sales_summary', {
                'start': '2026-10-01', 'end': '2026-10-31',
            })
            assert not summary.isError
            assert summary.structuredContent['result'][0]['orders'] == 4
            assert str(summary.structuredContent['result'][0]['revenue']) == '5500.00'
            top = await client.call_tool('top_products', {
                'start': '2026-10-01', 'end': '2026-10-31', 'limit': 2,
            })
            assert not top.isError
            assert [r['product'] for r in top.structuredContent['result']] == ['JavaScript', 'Python']
            blocked = await client.call_tool('execute_sql', {'sql': 'SELECT * FROM private.orders'})
            assert blocked.isError
            invalid = await client.call_tool('top_products', {
                'start': '2026-10-01', 'end': '2026-10-31', 'limit': 100,
            })
            assert invalid.isError

@pytest.mark.skipif(not os.getenv('DATABASE_URL'), reason='Requires demo PostgreSQL')
def test_all_business_tables_are_private():
    import psycopg
    with psycopg.connect(os.environ['DATABASE_URL'], autocommit=True) as conn:
        conn.execute('SET default_transaction_read_only = off')
        for table in ('customers', 'categories', 'products', 'orders', 'order_items', 'payments'):
            for operation in ('SELECT * FROM', 'DELETE FROM'):
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    conn.execute(f'{operation} private.{table}')
        assert conn.execute("SELECT * FROM api.sales_summary('2026-10-05','2026-10-06')").fetchone() == (0, 0)
