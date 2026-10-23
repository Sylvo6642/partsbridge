# Matching eval: `matching_v4`

Date: 2026-10-23 · dataset `matching_holdout` · 12 buyer lines · model gpt-4o-mini · max 5 model calls per line

| Metric | Baseline (search #1) | Agent |
|---|---|---|
| Correct decision | 6/12 (50%) | 10/12 (83%) |
| **Confidently wrong** (lower is better) | 6 | 1 |
| Right options offered when asking | n/a | 100% |
| Guardrail overrides | n/a | 0 |
| Model calls per line (avg) | 0 | 2.8 |
| Tool calls per line (avg) | 0 | 1.9 |
| Cost per line (avg) | ~$0.000001 | $0.00085 |
| Latency per line (avg) | <0.5 s | 4.8 s |

## By line type

| Type | n | Baseline | Agent |
|---|---|---|---|
| exact code | 2 | 1/2 | 2/2 |
| code + words | 1 | 1/1 | 1/1 |
| brand | 1 | 1/1 | 0/1 |
| description | 3 | 3/3 | 3/3 |
| ambiguous | 3 | 0/3 | 3/3 |
| not in catalog | 2 | 0/2 | 1/2 |

## Agent mistakes

- **h04** (brand) ` B belt 46 inch`: said needs_choice, expected matched. Agent's reason: Multiple lengths available; specify exact length.
- **h12** (not in catalog) ` 18.5 kW 4 pole motor B3`: picked Norvik NM3-160M-4P-11KW-B3 but should be not_found. Agent's reason: The buyer specified 18.5 kW, which is not available; options are lower power ratings.
