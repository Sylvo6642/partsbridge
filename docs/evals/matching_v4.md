# Matching eval: `matching_v4`

Date: 2026-10-23 · dataset `matching` · 32 buyer lines · model gpt-4o-mini · max 5 model calls per line

| Metric | Baseline (search #1) | Agent |
|---|---|---|
| Correct decision | 13/32 (41%) | 28/32 (88%) |
| **Confidently wrong** (lower is better) | 19 | 0 |
| Right options offered when asking | n/a | 92% |
| Guardrail overrides | n/a | 0 |
| Model calls per line (avg) | 0 | 2.7 |
| Tool calls per line (avg) | 0 | 1.7 |
| Cost per line (avg) | ~$0.000001 | $0.00078 |
| Latency per line (avg) | <0.5 s | 4.1 s |

## By line type

| Type | n | Baseline | Agent |
|---|---|---|---|
| exact code | 6 | 5/6 | 6/6 |
| code + words | 4 | 3/4 | 4/4 |
| brand | 3 | 1/3 | 3/3 |
| description | 7 | 4/7 | 6/7 |
| ambiguous | 6 | 0/6 | 6/6 |
| not in catalog | 6 | 0/6 | 3/6 |

## Agent mistakes

- **m19** (description) ` classical V-belt B section 62 inch`: said not_found, expected matched. Agent's reason: No V-belt with section B and 62 inch length found.
- **n01** (not in catalog) `6211-2RS1 bearing`: said needs_choice, expected not_found. Agent's reason: Missing bore and outer diameter specifications.
- **n02** (not in catalog) ` SPZ wedge belt 1000 mm`: said needs_choice, expected not_found. Agent's reason: Two different sections (SPB and SPA) available for 1000 mm length.
- **n06** (not in catalog) `6312ZZ bearing`: said needs_choice, expected not_found. Agent's reason: Missing bore and outer diameter specifications.
