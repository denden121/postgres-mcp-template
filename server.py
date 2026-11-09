"""Launch from the repository with: uv run python server.py."""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from mcp.server.fastmcp import FastMCP
from postgres_mcp.database import execute as database_execute
from postgres_mcp.operations.sales import register, validate_dates

mcp = FastMCP('Safe sales analytics')


def execute(operation, params):
    return database_execute(operation, params)


sales_summary, top_products = register(mcp, lambda name, params: execute(name, params))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    mcp.run(transport='stdio')
