# Extraction eval: `extraction_v3`

Date: 2026-10-23 · Model: gpt-4o-mini · Dataset: `extraction_holdout`, 10 cases, 17 line items

| Metric | Value |
|---|---|
| Cases fully correct | 9/10 (90%) |
| Item precision | 100.0% |
| Item recall | 100.0% |
| Item F1 | 100.0% |
| Quantity correct (matched items) | 100.0% |
| Brand correct (matched items) | 100.0% |
| Part number correct (matched items) | 94.1% |
| Retries needed | 1 |
| Crashes | 0 |
| Total cost | $0.0017 |
| Avg latency per case | 1909 ms |

## Failures

- **h04** (no part number): filter: part_number '3/4-16', expected None
