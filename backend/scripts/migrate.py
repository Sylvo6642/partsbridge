"""Apply the SQL files in supabase/migrations/ that have not run yet, in name order.

Run from backend/:  python -m scripts.migrate
"""

from pathlib import Path

from app.db import connect

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "supabase" / "migrations"


def main() -> None:
    with connect() as conn:
        conn.execute("create table if not exists schema_migrations (name text primary key, applied_at timestamptz default now())")
        done = {row[0] for row in conn.execute("select name from schema_migrations")}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in done:
                continue
            print(f"applying {path.name}")
            conn.execute(path.read_text(encoding="utf-8"))
            conn.execute("insert into schema_migrations (name) values (%s)", (path.name,))
        print("database is up to date")


if __name__ == "__main__":
    main()
