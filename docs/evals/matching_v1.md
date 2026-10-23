# Matching eval: `matching_v1`

Date: 2026-10-23 · 32 buyer lines · model gpt-4o-mini · max 5 model calls per line

| Metric | Baseline (search #1) | Agent |
|---|---|---|
| Correct decision | 13/32 (41%) | 12/32 (38%) |
| **Confidently wrong** (lower is better) | 19 | 0 |
| Right options offered when asking | n/a | 69% |
| Guardrail overrides | n/a | 2 |
| Model calls per line (avg) | 0 | 3.4 |
| Tool calls per line (avg) | 0 | 3.7 |
| Cost per line (avg) | ~$0.000001 | $0.00093 |
| Latency per line (avg) | <0.5 s | 4.6 s |

## By line type

| Type | n | Baseline | Agent |
|---|---|---|---|
| exact code | 6 | 5/6 | 1/6 |
| code + words | 4 | 3/4 | 0/4 |
| brand | 3 | 1/3 | 2/3 |
| description | 7 | 4/7 | 0/7 |
| ambiguous | 6 | 0/6 | 6/6 |
| not in catalog | 6 | 0/6 | 3/6 |

## Agent mistakes

- **m01** (exact code) `6205DDU bearing`: said needs_choice, expected matched. Agent's reason: Multiple equivalent parts available with the same specifications.
- **m02** (exact code) `spb2250 belts`: said needs_choice, expected matched. Agent's reason: Multiple brands available for the same part number.
- **m03** (exact code) `FR250/10 filter element`: said needs_choice, expected matched. Agent's reason: Multiple brands available for the same specifications.
- **m05** (exact code) `A-42 V-belt`: said needs_choice, expected matched. Agent's reason: Multiple brands available for the same part.
- **m06** (exact code) `6310 open bearing`: said needs_choice, expected matched. Agent's reason: Multiple brands available for the specified part.
- **m07** (code + words) `6205 sealed bearing`: said needs_choice, expected matched. Agent's reason: Multiple sealed options available.
- **m08** (code + words) `6207 bearing with metal shields`: said needs_choice, expected matched. Agent's reason: Multiple options available with metal shields.
- **m09** (code + words) `6302 open bearing`: said needs_choice, expected matched. Agent's reason: Multiple brands available for the same part.
- **m10** (code + words) `6001 2RS bearing`: said needs_choice, expected matched. Agent's reason: Multiple brands available for the specified bearing.
- **m13** (brand) `6205-2RS1 bearing`: said not_found, expected matched. Agent's reason: The agent did not finish.
- **m14** (description) ` 1.5 kW 4 pole motor, foot mounted`: said needs_choice, expected matched. Agent's reason: Multiple brands available for the specified motor.
- **m15** (description) ` hydraulic return filter element 10 micron 400mm long`: said needs_choice, expected matched. Agent's reason: Multiple brands available for the same specifications.
- **m16** (description) ` spin-on oil filter 3/4-16 UNF 140mm high`: said needs_choice, expected matched. Agent's reason: Multiple options available for the specified filter.
- **m17** (description) ` 11 kW 2 pole motor flange mount`: said needs_choice, expected matched. Agent's reason: Multiple options available for 11 kW 2-pole flange mount motor.
- **m18** (description) ` sealed bearing 40 x 90 x 23 mm`: said needs_choice, expected matched. Agent's reason: Multiple sealed bearings match the specifications.
- **m19** (description) ` classical V-belt B section 62 inch`: said needs_choice, expected matched. Agent's reason: Multiple brands available for the same specifications.
- **m20** (description) ` air filter element 160 mm x 300 mm`: said needs_choice, expected matched. Agent's reason: Multiple brands available for the specified dimensions.
- **n02** (not in catalog) ` SPZ wedge belt 1000 mm`: said needs_choice, expected not_found. Agent's reason: Buyer did not specify the belt section (SPA or SPB).
- **n03** (not in catalog) ` 15 kW 4 pole motor foot mounted`: said needs_choice, expected not_found. Agent's reason: Multiple 4 kW motors available, but none match 15 kW.
- **n05** (not in catalog) ` hydraulic return filter 5 micron 250 mm`: said needs_choice, expected not_found. Agent's reason: No filter with 5 micron specification found.
