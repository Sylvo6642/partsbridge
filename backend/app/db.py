"""Database connection (Supabase Postgres)."""

import psycopg

from app.config import settings


def connect() -> psycopg.Connection:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set. Copy .env.example to .env and fill it in.")
    return psycopg.connect(settings.database_url)
