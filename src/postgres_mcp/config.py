import os
from pathlib import Path
from dotenv import load_dotenv


def database_url() -> str:
    load_dotenv(Path(__file__).resolve().parents[2] / '.env', override=False)
    value = os.getenv('DATABASE_URL', '')
    if not value:
        raise ValueError('Set DATABASE_URL in environment or .env')
    return value
