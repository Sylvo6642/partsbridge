# Matching eval: `matching_v2`

Date: 2026-10-23 · 32 buyer lines · model gpt-4o-mini · max 5 model calls per line

| Metric | Baseline (search #1) | Agent |
|---|---|---|
| Correct decision | 13/32 (41%) | 21/32 (66%) |
| **Confidently wrong** (lower is better) | 19 | 0 |
| Right options offered when asking | n/a | 92% |
| Guardrail overrides | n/a | 0 |
| Model calls per line (avg) | 0 | 2.2 |
| Tool calls per line (avg) | 0 | 1.2 |
| Cost per line (avg) | ~$0.000001 | $0.00050 |
| Latency per line (avg) | <0.5 s | 2.9 s |

## By line type

| Type | n | Baseline | Agent |
|---|---|---|---|
| exact code | 6 | 5/6 | 4/6 |
| code + words | 4 | 3/4 | 3/4 |
| brand | 3 | 1/3 | 3/3 |
| description | 7 | 4/7 | 2/7 |
| ambiguous | 6 | 0/6 | 6/6 |
| not in catalog | 6 | 0/6 | 3/6 |

## Agent mistakes

- **m01** (exact code) `6205DDU bearing`: said needs_choice, expected matched. Agent's reason: Multiple sealing options available.
- **m03** (exact code) `FR250/10 filter element`: said needs_choice, expected matched. Agent's reason: Multiple filter elements match but differ in micron rating.
- **m07** (code + words) `6205 sealed bearing`: said needs_choice, expected matched. Agent's reason: Buyer specified 'sealed' but did not indicate a preference for brand.
- **m15** (description) ` hydraulic return filter element 10 micron 400mm long`: said needs_choice, expected matched. Agent's reason: Multiple brands available for the specified filter length and micron rating.
- **m16** (description) ` spin-on oil filter 3/4-16 UNF 140mm high`: said needs_choice, expected matched. Agent's reason: Multiple options available; buyer needs to specify brand preference.
- **m17** (description) ` 11 kW 2 pole motor flange mount`: said not_found, expected matched. Agent's reason: No 11 kW motor found in the catalog.
- **m18** (description) ` sealed bearing 40 x 90 x 23 mm`: said needs_choice, expected matched. Agent's reason: Multiple sealing options available.
- **m19** (description) ` classical V-belt B section 62 inch`: said needs_choice, expected matched. Agent's reason: Multiple options available for section B, but buyer specified only length.
- **n02** (not in catalog) ` SPZ wedge belt 1000 mm`: said needs_choice, expected not_found. Agent's reason: The section type (SPA or SPB) is missing.
- **n04** (not in catalog) ` variable frequency drive 5.5 kW`: said needs_choice, expected not_found. Agent's reason: Missing mounting type (B3 or B5).
- **n05** (not in catalog) ` hydraulic return filter 5 micron 250 mm`: said needs_choice, expected not_found. Agent's reason: Different micron ratings available.
