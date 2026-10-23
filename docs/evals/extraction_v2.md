# Extraction eval: `extraction_v2`

Date: 2026-10-23 · Model: gpt-4o-mini · Dataset: 20 cases, 32 line items

| Metric | Value |
|---|---|
| Cases fully correct | 16/20 (80%) |
| Item precision | 87.5% |
| Item recall | 87.5% |
| Item F1 | 87.5% |
| Quantity correct (matched items) | 100.0% |
| Brand correct (matched items) | 100.0% |
| Part number correct (matched items) | 100.0% |
| Retries needed | 0 |
| Crashes | 0 |
| Total cost | $0.0029 |
| Avg latency per case | 1799 ms |

## Failures

- **e02** (email): missed 6205DDU; extra item '6205'
- **e06** (typos): missed 6206 2rs; extra item '6206'
- **e08** (no quantity): missed 6309DDU; extra item '6309'
- **e18** (german): missed 6207-2RSR; extra item '6207'
