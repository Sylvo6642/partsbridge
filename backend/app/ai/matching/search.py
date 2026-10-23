"""Catalog search: three ways to find a part, and one way to combine them.

- by_part_number: exact (then prefix) match on the normalized part number. Precise, but only works with a code.
- by_keyword:     Postgres full-text search. Good when the buyer uses the same words as the catalog.
- by_meaning:     embeddings + pgvector. Good when the words differ but the meaning is the same.
- hybrid:         runs all three and merges the rankings with Reciprocal Rank Fusion (RRF).
"""

import re
from dataclasses import dataclass, field

import psycopg

from app.ai.llm import embed
from app.part_numbers import normalize_part_number

COLUMNS = "id, brand, part_number, category, description, interchange_group"
RRF_K = 60  # standard RRF constant: higher = later ranks count relatively more


@dataclass
class Hit:
    part_id: int
    brand: str
    part_number: str
    category: str
    description: str
    interchange_group: str
    score: float = 0.0
    found_by: list[str] = field(default_factory=list)


def _hits(rows, method: str) -> list[Hit]:
    return [Hit(*row, found_by=[method]) for row in rows]


def _codes(text: str, part_number: str | None) -> list[str]:
    """Candidate part numbers: the extracted one if we have it, else any token that contains a digit."""
    if part_number:
        return [normalize_part_number(part_number)]
    tokens = [normalize_part_number(t) for t in text.split()]
    return [t for t in tokens if len(t) >= 3 and any(c.isdigit() for c in t)]


def by_part_number(conn: psycopg.Connection, text: str, part_number: str | None = None,
                   limit: int = 20) -> list[Hit]:
    codes = _codes(text, part_number)
    if not codes:
        return []
    # Exact matches first, then parts whose number starts with the code ("6205" -> "6205DDU").
    rows = conn.execute(
        f"""select {COLUMNS} from parts
            where part_number_norm = any(%(codes)s)
               or part_number_norm like any(%(prefixes)s)
            order by (part_number_norm = any(%(codes)s)) desc, length(part_number_norm), id
            limit %(limit)s""",
        {"codes": codes, "prefixes": [c + "%" for c in codes], "limit": limit},
    ).fetchall()
    return _hits(rows, "part_number")


def by_keyword(conn: psycopg.Connection, text: str, limit: int = 20) -> list[Hit]:
    words = re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower())  # keep decimals: "1.5" stays "1.5"
    if not words:
        return []
    # OR the words together: a part doesn't need every word, but more matching words rank higher.
    rows = conn.execute(
        f"""with q as (select to_tsquery('english', %s) as query)
            select {COLUMNS} from parts, q
            where search_tsv @@ q.query
            order by ts_rank_cd(search_tsv, q.query) desc, id
            limit %s""",
        (" | ".join(words), limit),
    ).fetchall()
    return _hits(rows, "keyword")


def embed_query(text: str) -> list[float]:
    return embed([text], feature="search_query")[0]


def by_meaning(conn: psycopg.Connection, query_vector: list[float], limit: int = 20) -> list[Hit]:
    rows = conn.execute(
        f"select {COLUMNS} from parts where embedding is not null order by embedding <=> %s::vector limit %s",
        (str(query_vector), limit),
    ).fetchall()
    return _hits(rows, "meaning")


def rrf(rankings: list[list[Hit]], limit: int = 10) -> list[Hit]:
    """Reciprocal Rank Fusion: each list gives a part 1 / (60 + rank). Parts found by several lists rise."""
    merged: dict[int, Hit] = {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, start=1):
            entry = merged.setdefault(hit.part_id, Hit(**{**hit.__dict__, "score": 0.0, "found_by": []}))
            entry.score += 1 / (RRF_K + rank)
            entry.found_by += hit.found_by
    return sorted(merged.values(), key=lambda h: h.score, reverse=True)[:limit]


def hybrid(conn: psycopg.Connection, text: str, part_number: str | None = None,
           query_vector: list[float] | None = None, limit: int = 10) -> list[Hit]:
    query_vector = query_vector or embed_query(text)
    return rrf([by_part_number(conn, text, part_number), by_keyword(conn, text),
                by_meaning(conn, query_vector)], limit=limit)
