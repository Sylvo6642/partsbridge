# Day 1: setup and a synthetic catalog

## What I built
- The repo, folder layout and docs (README, decisions, this journal, eval tracker, demo walkthrough).
- **A catalog generator** (`backend/scripts/generate_catalog.py`): 621 parts in 4 categories (bearings, V-belts,
  filters, motors) from 3 fictional brands, 5 sellers, 1,321 offers (price, stock, lead time).
- **The first database migration** (`supabase/migrations/0001_catalog.sql`): `sellers`, `parts`, `offers`, with
  pgvector turned on and Row Level Security on every table.
- Scripts to apply migrations and load the CSVs into Supabase.
- 6 tests on the data (same seed gives the same data, part numbers are unique, interchangeable parts have the same specs, …).

## Concepts, in plain words

**Why synthetic data that looks real?** Real catalogs are private. But if the fake data is too clean, the AI has
nothing hard to do. So the brands are made up, but the part-number *rules* are real. A `6205` bearing is always
25 × 52 × 15 mm. Each brand writes the seal type differently:

| Brand | Same physical part (6205, rubber seals) |
|---|---|
| Norvik | `6205-2RS1` |
| Kanto Seiko | `6205DDU` |
| Ferrum | `6205-2RSR` |

A buyer might write any of these, or "6205 2rs", or "sealed bearing 25mm shaft". That's the matching problem for Days 3–4.

**Interchange groups.** The three rows above share `interchange_group = bearing:6205:sealed`. That is the whole
"cross-reference" system: to find an equivalent part, look for other parts in the same group. The future tool
`find_equivalent` is one SQL query.

**Part-number normalization.** `6205-2RS1`, `6205 2rs1` and `6205.2RS1` all become `62052RS1`. Exact lookup on the
normalized form is the cheapest and most reliable search there is. RAG comes after it, not instead of it.

**Fixed random seed.** The generator uses `random.Random(42)`. Every run produces the exact same catalog, so a test
score from Day 3 and one from Day 6 are measured against the same data.

**Row Level Security (RLS).** Supabase lets the browser talk to the database directly, so every table needs rules.
With RLS on and no rule, nobody can read the table (except the backend's admin connection). Parts are public;
prices and stock stay private. This is the base of "the AI never decides who can see what" (D-004).

**Money is never a float.** Prices are `Decimal` in Python and `numeric(12,2)` in Postgres.

## Something I noticed
The open (unsealed) bearing is just `6205` for all three brands. So a buyer typing "6205" matches three parts that
are all correct. The matcher on Day 4 has to understand that this is fine (same group), not a confusing tie.

## Numbers
- 621 parts · 207 interchange groups · 5 sellers · 1,321 offers
- 6/6 tests pass
- Loaded into Supabase (Postgres 17). Exact lookup `62052RS1` → Norvik `6205-2RS1`; the equivalents of `6205DDU` are
  the 3 sealed 6205s.
- RLS check through the public API with the browser key: `parts` returns rows, `offers` returns **0 rows**.
  Prices are private, as intended.
- AI cost today: $0 (no model calls yet)

## Next (Day 2)
Extraction: turn a messy pasted request into a checked parts list with structured outputs, build a labelled test
set, and get the first score.
