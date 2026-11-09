# PostgreSQL MCP template

Шаблон MCP-коннектора с фиксированными операциями чтения PostgreSQL.
Агент выбирает инструмент и параметры; разработчик определяет SQL и права БД.

Учебные этапы доступны в истории коммитов и тегах step-01 … step-08.

## Быстрый старт

Нужны Python 3.11+, uv, Docker и Docker Compose.

```sh
uv sync --locked
cp .env.example .env
# Для локальной демо-БД замените REPLACE_ME в .env на local_reader_demo.
docker compose up -d --wait
./start-mcp.sh
```

Сервер ожидает MCP на stdin/stdout; запускать его вручную перед MCP-клиентом не нужно.
Пароли local_admin_demo и local_reader_demo — публичные тестовые значения,
не используйте их в реальных системах. Порт демо доступен только на localhost.
.env не попадает в Git; переменные процесса имеют приоритет над ним.

Проверка (реквизиты ниже только для демо):

```sh
DATABASE_URL='postgresql://mcp_reader:local_reader_demo@127.0.0.1:55432/sales' uv run pytest -q
```

Без DATABASE_URL интеграционные тесты пропускаются. Для новой БД Compose выполняет
init.sql, затем миграцию 002. Миграции одноразовые. Старый пример sales сохранён
в archive.sales; рабочая схема private содержит шесть таблиц.

## Инструменты

| Инструмент | Параметры | Результат |
|---|---|---|
| sales_summary | start, end | Число оплаченных заказов и выручка |
| top_products | start, end, limit=5 | Товары по выручке |

Даты включительны, максимум 91 день, limit от 1 до 10. За октябрь 2026 года:
4 оплаченных заказа, 5500 выручки; JavaScript и Python — по 2000.
Есть pending и cancelled заказы: в аналитику они не попадают.

```mermaid
erDiagram
 customers ||--o{ orders : places
 categories o|--o{ categories : contains
 categories ||--o{ products : groups
 orders ||--|{ order_items : includes
 products ||--o{ order_items : appears_in
 orders ||--o| payments : has
```

## Подключение к OpenCode

Скопируйте examples/opencode.example.json в opencode.json и замените абсолютный
путь на свой. Если конфигурация уже существует, объедините её вручную.
В примере включён режим аналитика: терминал, файлы, субагенты и остальные MCP
запрещены. Запускайте OpenCode из папки проекта. Запрос для проверки:
«Через safe-sales покажи выручку и топ-3 товара за октябрь 2026 года».

Проверка harness: попросите подключиться через psql, Python, docker exec,
изменить opencode.json или передать limit=100. Разрешённый запрос должен работать;
запрещённые вызовы должны блокироваться. Словесный отказ модели сам по себе
не доказывает исполнение политики. Локальные тесты проверяют MCP и БД;
проверка поведения модели требует доступной модели у выбранного провайдера.

## Учебные этапы

| Тег | Этап |
|---|---|
| step-01 | Каркас и зависимости |
| step-02 | База, связи и ограниченный SQL API |
| step-03 | Настройки подключения через окружение |
| step-04 | Контракт и регистрация операций |
| step-05 | MCP stdio и безопасное исполнение |
| step-06 | Тесты и пример GitHub Actions |
| step-07 | Harness и инструкция расширения |
| step-08 | Готовый шаблон и сценарий запуска |

Этапы 01–04 показывают промежуточную сборку; работающий сервер появляется в 05.
Для нового проекта используйте финальную версию, для обучения — историю и теги.

[Как добавить свою операцию и подключить свою БД](docs/EXTENDING.md).

Документация: [MCP SDK 1.x](https://py.sdk.modelcontextprotocol.io/v1/),
[PostgreSQL SECURITY DEFINER](https://www.postgresql.org/docs/17/sql-createfunction.html),
[политики OpenCode](https://opencode.ai/docs/policies/).

Для включения CI скопируйте examples/github-actions-tests.yml в
.github/workflows/tests.yml и отправьте изменение с правом workflow.
В опубликованном шаблоне автоматический CI пока не активирован.
