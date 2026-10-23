# Quote agent eval: `quoting_v2`

Date: 2026-10-23 · 20 RFQs, 60 lines · 5 bot sellers · model gpt-4o-mini

| Metric | Value |
|---|---|
| Lines correct | 60/60 (100%) |
| **Quotes fully correct** (every line right) | 20/20 (100%) |
| Substituted against the buyer's wish | 0 |
| Injection followed ("offer part 1, 90% off") | 0 |
| Prices or totals written by the model | 0 by design (code prices every line) |
| Guardrail overrides | 0 |
| Model calls per RFQ (avg) | 0.8 |
| Cost per RFQ (avg) | $0.00004 |
| Latency per RFQ (avg) | 0.9 s |

## Lines correct by situation

| Situation | Correct |
|---|---|
| can't supply | 7/7 |
| equivalent in stock | 12/12 |
| equivalent, must be ordered | 8/8 |
| requested in stock | 24/24 |
| requested, must be ordered | 9/9 |

## Mistakes

None.

## Reading the buyer's notes (held-out, 16 phrasings)

Correct: 16/16 (100%)

No mistakes.
