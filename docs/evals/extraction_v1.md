# Extraction eval: `extraction_v1`

Date: 2026-10-23 · Model: gpt-4o-mini · Dataset: 20 cases, 32 line items

| Metric | Value |
|---|---|
| Cases fully correct | 15/20 (75%) |
| Item precision | 87.1% |
| Item recall | 84.4% |
| Item F1 | 85.7% |
| Quantity correct (matched items) | 100.0% |
| Brand correct (matched items) | 96.3% |
| Part number correct (matched items) | 100.0% |
| Retries needed | 0 |
| Crashes | 0 |
| Total cost | $0.0024 |
| Avg latency per case | 2030 ms |

## Failures

- **e02** (email): missed A42; extra item 'A42 V-belt'
- **e04** (quantity words): missed B60; extra item 'B60 belts'
- **e05** (brand): 6305-2RS1: brand None, expected 'Norvik'; missed SPB1500
- **e14** (similar parts): missed 6310; extra item '6310 open'
- **e18** (german): missed SPA1250; extra item 'Keilriemen SPA1250'
