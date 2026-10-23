# Evals

Each AI feature has a labelled test set (input + right answer) in `backend/evals/datasets/` and a script that
prints a score. Each run is saved here as a dated report, so progress is visible over time.

| Feature | Metric | Latest score | Day |
|---|---|---|---|
| Extraction | Fields correct (F1) | not yet | 2 |
| Catalog search | Right part in top 5 (Recall@5) | not yet | 3 |
| Part matching agent | Right part chosen; abstains when unsure | not yet | 4 |
| Quote agent | Total exactly right | not yet | 6 |
| Safety | Injection attacks that succeed (target 0) | not yet | 7 |
