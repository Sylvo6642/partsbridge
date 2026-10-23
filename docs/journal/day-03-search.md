# Day 3: catalog search (keyword + meaning, combined)

## What I built
- Migration `0003`: a full-text search column (`search_tsv`, GIN index) and an embedding column (`vector(1536)`,
  HNSW index) on `parts`.
- `llm.embed()` and `scripts/embed_catalog.py`: all 621 parts embedded with text-embedding-3-small for **$0.0006**.
- `app/ai/matching/search.py`: three searches plus a combiner:
  - `by_part_number`: normalized exact match, then prefix ("6205" → 6205DDU, 6205-2RS1, …)
  - `by_keyword`: Postgres full-text search
  - `by_meaning`: embeddings, nearest vectors by cosine distance (pgvector)
  - `hybrid`: all three merged with **Reciprocal Rank Fusion (RRF)**
- An eval of 40 labelled queries in 5 types (exact code, messy code, code + words, description, synonyms), and
  `evals/run_search.py`, which scores every method separately.
- `GET /search?q=` on the API.

## Concepts, in plain words

**Embeddings.** A model turns text into 1536 numbers. Texts with similar meaning end up with similar numbers, so
"ball bearing for 20mm shaft" lands near "deep groove ball bearing, 20 mm bore". Search = embed the query, then find
the closest part vectors. pgvector does this inside Postgres; the HNSW index makes it fast.

**Full-text search.** Postgres splits text into words and reduces them to stems ("bearings" → "bearing",
"sealed" → "seal"). Fast and exact about words, but it knows nothing about meaning.

**Why combine?** Each method fails on different queries. Exact part-number search is perfect when there's a code and
useless when there isn't. Meaning search handles synonyms but is fuzzy about numbers.

**RRF (Reciprocal Rank Fusion).** Every method returns a ranked list. Each part gets `1 / (60 + rank)` from every
list it appears in, and the scores are added up. A part that shows up in several lists rises to the top. It only uses
ranks, not raw scores, so there's no need to make "keyword score 0.3" comparable with "cosine distance 0.21".

**Recall@5 and MRR.** Recall@5: is a correct part in the top 5? MRR: on average, how high is the first correct part?
1.0 = always first, 0.5 = usually second. A result counts as correct if it is the right physical part from **any**
brand (same `interchange_group`).

## Results

| Method | v1 Recall@5 | v1 MRR | v2 Recall@5 | v2 MRR |
|---|---|---|---|---|
| Part number | 42% | 0.41 | 42% | 0.41 |
| Keyword | 78% | 0.69 | 85% | 0.79 |
| Meaning | 88% | 0.78 | 85% | 0.76 |
| **Hybrid (RRF)** | **92%** | **0.82** | **98%** | **0.87** |

By query type (v2, Recall@5): part-number search scores 100% on codes and 0% on descriptions. Keyword is weak on messy
codes (50%). Hybrid is ≥ 91% on every type. Full reports: [v1](../evals/search_v1.md), [v2](../evals/search_v2.md).

## The two bugs the eval found (v1 → v2)
1. **"Sealed" matched the open bearing.** The open bearing's text said "open (no seals)". Full-text search reduces
   "seals" and "sealed" to the same stem, and embeddings don't handle "no" well either. So "6205 sealed bearing" put
   three *open* 6205s first. Fix: the catalog now says "open type, unsealed and unshielded". **Lesson: negation in
   your documents hurts both kinds of search.**
2. **"1.5 kW" became "1" and "5".** My keyword splitter dropped the decimal point, so motor queries lost their key
   number. "1.5 kW 4 pole motor" wasn't even in the top 10. Fix: keep decimals.

Honest caveat: I changed data and code after looking at these 40 queries, so v2's numbers are a little optimistic.
Both fixes are general (any negation, any decimal), not tuned to specific queries. Meaning search dropped from 88%
to 85% because the new catalog text changed the embeddings.

## What search can't do (Day 4's job)
The misses that remain are the right kind of part at the wrong size: a 250 mm filter ranked above the 400 mm one, a
4 kW motor above 1.5 kW. Embeddings and keywords are fuzzy about numbers. And some requests are truly ambiguous:
"sealed bearing for 25 mm shaft" fits both a 6005 and a 6205 (same bore, different outer diameter). Search gives the
**candidates**. The Day 4 agent reads their specs, picks one, or asks the buyer.

## Numbers
- Hybrid search: Recall@5 **98%**, MRR **0.87** (40 queries)
- Embedding the whole catalog: $0.0006. One search query costs about $0.000001 to embed
- 15/15 unit tests pass

## Note
`load_catalog` replaces every part, so it wipes the embeddings. Run `python -m scripts.embed_catalog` after it.

## Next (Day 4)
The part-matching agent: tools `search_catalog` and `find_equivalent`. It compares candidate specs with the
request, gives a confidence score, and asks the buyer when unsure.
