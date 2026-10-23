"""Database connections (Supabase Postgres).

- connect():      the backend's own connection. It bypasses Row Level Security, so it is only used for
                  system jobs: migrations, seeding a new workspace, bot sellers, AI call logs.
- as_user(id):    everything a visitor triggers. It switches to Supabase's `authenticated` role and sets the
                  user id, so Postgres applies RLS: queries only see that visitor's rows.
"""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

import psycopg

from app.config import settings


def connect() -> psycopg.Connection:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set. Copy .env.example to .env and fill it in.")
    return psycopg.connect(settings.database_url)


@contextmanager
def as_user(user_id: UUID) -> Iterator[psycopg.Connection]:
    """A connection (one transaction) that runs with the visitor's identity, so RLS applies."""
    with connect() as conn:
        claims = json.dumps({"sub": str(user_id), "role": "authenticated"})
        conn.execute("select set_config('request.jwt.claims', %s, true)", (claims,))
        conn.execute("set local role authenticated")
        yield conn
