from datetime import date

QUERIES = {
    'sales_summary': 'SELECT * FROM api.sales_summary(%s::date, %s::date)',
    'top_products': 'SELECT * FROM api.top_products(%s::date, %s::date, %s::integer)',
}


def validate_dates(start: date, end: date):
    if not 0 <= (end - start).days <= 90:
        raise ValueError('Период должен быть от 1 до 91 календарного дня включительно')


def register(mcp, execute):
    from typing import Annotated
    from pydantic import Field

    @mcp.tool()
    def sales_summary(start: date, end: date) -> list[dict]:
        """Количество оплаченных заказов и выручка по дате заказа, максимум 91 день."""
        validate_dates(start, end)
        return execute('sales_summary', (start, end))

    @mcp.tool()
    def top_products(start: date, end: date,
                     limit: Annotated[int, Field(strict=True, ge=1, le=10)] = 5) -> list[dict]:
        """Топ товаров оплаченных заказов, максимум 91 день и 10 товаров."""
        validate_dates(start, end)
        if type(limit) is not int or not 1 <= limit <= 10:
            raise ValueError('Лимит должен быть целым числом от 1 до 10')
        return execute('top_products', (start, end, limit))

    return sales_summary, top_products
