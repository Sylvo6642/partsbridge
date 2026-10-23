# Evals

Each AI feature has a labelled test set (input + right answer) in `backend/evals/datasets/` and a script that
prints a score. Each run is saved here as a dated report, so progress is visible over time.

| Feature | Metric | Latest score | Day |
|---|---|---|---|
| Extraction | Cases fully correct · item F1 | prompt v3: tuning 20/20 · held-out 9/10 · F1 100% ([report](extraction_v3.md), [held-out](extraction_v3-extraction_holdout.md)) | 2 |
| Catalog search | Right part in top 5 (Recall@5) | not yet | 3 |
| Part matching agent | Right part chosen; abstains when unsure | not yet | 4 |
| Quote agent | Total exactly right | not yet | 6 |
| Safety | Injection attacks that succeed (target 0) | not yet | 7 |

## History

| Date | Feature | Version | Tuning set | Held-out | Cost per message |
|---|---|---|---|---|---|
| 2026-10-23 | Extraction | v1 | 15/20 (F1 85.7%) | 10/10 | $0.00012 |
| 2026-10-23 | Extraction | v2 | 16/20 (F1 87.5%) | not run | $0.00014 |
| 2026-10-23 | Extraction | v3 | 20/20 (F1 100%) | 9/10 | $0.00016 |
