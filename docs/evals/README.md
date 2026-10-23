# Evals

Each AI feature has a labelled test set (input + right answer) in `backend/evals/datasets/` and a script that
prints a score. Each run is saved here as a dated report, so progress is visible over time.

| Feature | Metric | Latest score | Day |
|---|---|---|---|
| Extraction | Cases fully correct · item F1 | prompt v3: tuning 20/20 · held-out 9/10 · F1 100% ([report](extraction_v3.md), [held-out](extraction_v3-extraction_holdout.md)) | 2 |
| Catalog search | Right part in top 5 (Recall@5) · MRR | hybrid v2: 98% · 0.87 ([v1](search_v1.md), [v2](search_v2.md)) | 3 |
| Part matching agent | Correct decision · confidently wrong | v4: tuning 88% · 0 wrong; held-out 83% · 1 wrong (baseline 50% · 6) ([report](matching_v4.md), [held-out](matching_v4-matching_holdout.md)) | 4 |
| Quoting | Lines correct · quotes fully correct · unwanted substitutions | v2: 100% · 100% · 0 (v1 agent: 63% · 25% · 7); notes held-out 16/16 ([v2](quoting_v2.md), [v1](quoting_v1.md)) | 6 |
| Safety | Injection attacks that succeed (target 0) | not yet | 7 |

## History

| Date | Feature | Version | Tuning set | Held-out | Cost per message |
|---|---|---|---|---|---|
| 2026-10-23 | Extraction | v1 | 15/20 (F1 85.7%) | 10/10 | $0.00012 |
| 2026-10-23 | Extraction | v2 | 16/20 (F1 87.5%) | not run | $0.00014 |
| 2026-10-23 | Extraction | v3 | 20/20 (F1 100%) | 9/10 | $0.00016 |

### Catalog search (40 queries)

| Date | Version | Part number | Keyword | Meaning | Hybrid (Recall@5 / MRR) |
|---|---|---|---|---|---|
| 2026-10-23 | v1 | 42% | 78% | 88% | 92% / 0.82 |
| 2026-10-23 | v2 (no negation in catalog text, keep decimals) | 42% | 85% | 85% | 98% / 0.87 |

### Part matching (32 tuning lines; held-out 12)

| Date | Version | Correct | Confidently wrong | Cost per line |
|---|---|---|---|---|
| 2026-10-23 | Baseline: search #1, no AI | 41% (held-out 50%) | 19 (held-out 6) | ~$0 |
| 2026-10-23 | v1 flat search + find_equivalent | 38% | 0 | $0.00093 |
| 2026-10-23 | v2 results grouped by physical part | 66% | 0 | $0.00050 |
| 2026-10-23 | v3 + filter_catalog (exact specs) | 81% | 1 | $0.00091 |
| 2026-10-23 | v4 + code picks brand, catalog scope in prompt | 88% (held-out 83%) | 0 (held-out 1) | $0.00078 |

### Quoting (20 RFQs, 60 lines, 5 sellers; notes held-out 16)

| Date | Version | Lines correct | Quotes fully correct | Unwanted substitutions | Injection followed | Cost per RFQ |
|---|---|---|---|---|---|---|
| 2026-10-23 | v1 tool-calling agent | 63% | 25% | 7 | 0 | $0.00041 |
| 2026-10-23 | v2 AI reads notes, code decides | 100% | 100% | 0 | 0 | $0.00004 |
