"""Compute an embedding for every part that doesn't have one yet and store it in parts.embedding.

Run from backend/:  python -m scripts.embed_catalog        (add --all to recompute every part)
"""

import sys

from app.ai.llm import embed
from app.db import connect

BATCH = 200


def main() -> None:
    redo_all = "--all" in sys.argv
    with connect() as conn:
        where = "" if redo_all else "where embedding is null"
        rows = conn.execute(f"select id, name || '. ' || description from parts {where} order by id").fetchall()
        for i in range(0, len(rows), BATCH):
            batch = rows[i:i + BATCH]
            vectors = embed([text for _, text in batch], feature="catalog_embedding")
            with conn.cursor() as cur:
                cur.executemany("update parts set embedding = %s::vector where id = %s",
                                [(str(vec), part_id) for (part_id, _), vec in zip(batch, vectors)])
            print(f"embedded {i + len(batch)}/{len(rows)}")
        print("done")


if __name__ == "__main__":
    main()
