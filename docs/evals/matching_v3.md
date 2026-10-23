# Matching eval: `matching_v3`

Date: 2026-10-23 · 32 buyer lines · model gpt-4o-mini · max 5 model calls per line

| Metric | Baseline (search #1) | Agent |
|---|---|---|
| Correct decision | 13/32 (41%) | 26/32 (81%) |
| **Confidently wrong** (lower is better) | 19 | 1 |
| Right options offered when asking | n/a | 92% |
| Guardrail overrides | n/a | 0 |
| Model calls per line (avg) | 0 | 3.0 |
| Tool calls per line (avg) | 0 | 2.1 |
| Cost per line (avg) | ~$0.000001 | $0.00091 |
| Latency per line (avg) | <0.5 s | 4.6 s |

## By line type

| Type | n | Baseline | Agent |
|---|---|---|---|
| exact code | 6 | 5/6 | 6/6 |
| code + words | 4 | 3/4 | 4/4 |
| brand | 3 | 1/3 | 1/3 |
| description | 7 | 4/7 | 5/7 |
| ambiguous | 6 | 0/6 | 6/6 |
| not in catalog | 6 | 0/6 | 4/6 |

## Agent mistakes

- **m12** (brand) ` SPA belt 1250 mm`: said needs_choice, expected matched. Agent's reason: Multiple brands available; specify if a different brand is preferred.
- **m13** (brand) `6205-2RS1 bearing`: picked Norvik 6205-2RS1, wanted brand Kanto Seiko. Agent's reason: Exact match found for the specified bearing.
- **m16** (description) ` spin-on oil filter 3/4-16 UNF 140mm high`: said needs_choice, expected matched. Agent's reason: Multiple options available for the specified height and thread.
- **m19** (description) ` classical V-belt B section 62 inch`: said needs_choice, expected matched. Agent's reason: The length is slightly off; options are for 62 inch (1575 mm) V-belts.
- **n02** (not in catalog) ` SPZ wedge belt 1000 mm`: said needs_choice, expected not_found. Agent's reason: Two different sections (SPB and SPA) available for 1000 mm length.
- **n04** (not in catalog) ` variable frequency drive 5.5 kW`: said needs_choice, expected not_found. Agent's reason: Multiple mounting options available.
