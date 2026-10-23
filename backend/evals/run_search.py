"""Score each search method on the labelled queries.

Run from backend/:  python -m evals.run_search [--label v1]

A result is correct if it is in the expected interchange group (any brand of the right physical part).
- Recall@5: share of queries with a correct part in the top 5.
- MRR (mean reciprocal rank): average of 1/rank of the first correct part (top 10; 0 if not found).
  1.0 = always first, 0.5 = usually second.
"""

import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from app.ai.llm import embed
from app.ai.matching import search
from app.db import connect

DATASET = Path(__file__).parent / "datasets" / "search.jsonl"
REPORTS = Path(__file__).resolve().parents[2] / "docs" / "evals"
METHODS = ["part_number", "keyword", "meaning", "hybrid"]


def first_correct_rank(hits: list[search.Hit], expected_group: str, limit: int = 10) -> int | None:
    for rank, hit in enumerate(hits[:limit], start=1):
        if hit.interchange_group == expected_group:
            return rank
    return None


def run_method(conn, method: str, q: dict, vector: list[float]) -> list[search.Hit]:
    if method == "part_number":
        return search.by_part_number(conn, q["text"], q["part_number"])
    if method == "keyword":
        return search.by_keyword(conn, q["text"])
    if method == "meaning":
        return search.by_meaning(conn, vector)
    return search.hybrid(conn, q["text"], q["part_number"], query_vector=vector)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="v1", help="name for this run's report, e.g. v1")
    label = parser.parse_args().label

    queries = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]
    vectors = embed([q["text"] for q in queries], feature="eval_search")  # one call for all queries
    ranks: dict[str, list[int | None]] = defaultdict(list)
    misses: list[str] = []

    with connect() as conn:
        for q, vector in zip(queries, vectors):
            for method in METHODS:
                hits = run_method(conn, method, q, vector)
                rank = first_correct_rank(hits, q["expected_group"])
                ranks[method].append(rank)
                if method == "hybrid" and (rank is None or rank > 1):
                    top = ", ".join(f"{h.part_number} ({h.interchange_group})" for h in hits[:3])
                    misses.append(f"**{q['id']}** ({q['tag']}) `{q['text']}`: correct at rank "
                                  f"{rank or 'not in top 10'}. Top 3: {top}")

    def recall5(rs): return sum(r is not None and r <= 5 for r in rs) / len(rs)
    def mrr(rs): return sum(1 / r for r in rs if r) / len(rs)

    tags = list(dict.fromkeys(q["tag"] for q in queries))
    lines = [f"# Search eval: `{label}`", "",
             f"Date: {date.today()} · {len(queries)} queries · embeddings: text-embedding-3-small · RRF k={search.RRF_K}",
             "", "## Overall", "", "| Method | Recall@5 | MRR |", "|---|---|---|"]
    lines += [f"| {m} | {recall5(ranks[m]):.0%} | {mrr(ranks[m]):.2f} |" for m in METHODS]
    lines += ["", "## Recall@5 by query type", "", "| Query type | n | " + " | ".join(METHODS) + " |",
              "|---|---|" + "---|" * len(METHODS)]
    for tag in tags:
        idx = [i for i, q in enumerate(queries) if q["tag"] == tag]
        cells = [f"{recall5([ranks[m][i] for i in idx]):.0%}" for m in METHODS]
        lines.append(f"| {tag} | {len(idx)} | " + " | ".join(cells) + " |")
    lines += ["", "## Hybrid: queries where the right part was not ranked first", ""]
    lines += [f"- {m}" for m in misses] or ["None."]

    report = "\n".join(lines) + "\n"
    print(report)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"search_{label}.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
