"""Score the extractor against the labelled test set.

Run from backend/:  python -m evals.run_extraction [--prompt extraction_v1] [--dataset extraction_holdout]
Prints the score and writes a report to docs/evals/.

How an answer is scored:
- Each expected line item is matched to at most one predicted item: by part number (normalized) if it has one,
  otherwise by keywords that must appear in the predicted description.
- Item precision = matched / predicted, item recall = matched / expected, F1 combines both.
- For matched items we also check quantity, brand and part number.
- A case is "fully correct" when every item matches, there are no extras and every field is right.
"""

import argparse
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from app.ai.extraction import PROMPT_VERSION, LineItem, extract
from app.part_numbers import normalize_part_number

DATASETS = Path(__file__).parent / "datasets"
REPORTS = Path(__file__).resolve().parents[2] / "docs" / "evals"


@dataclass
class CaseScore:
    expected: int = 0
    predicted: int = 0
    matched: int = 0
    quantity_ok: int = 0
    brand_ok: int = 0
    part_number_ok: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def fully_correct(self) -> bool:
        return not self.errors


def _norm(value: str | None) -> str:
    return normalize_part_number(value or "")


def _same_brand(a: str | None, b: str | None) -> bool:
    return (a or "").strip().lower() == (b or "").strip().lower()


def _matches(expected: dict, item: LineItem) -> bool:
    if expected["part_number"]:
        return _norm(item.part_number) == _norm(expected["part_number"])
    text = f"{item.description} {item.part_number or ''}".lower()
    return all(k.lower() in text for k in expected["keywords"])


def score_case(expected_items: list[dict], predicted: list[LineItem]) -> CaseScore:
    s = CaseScore(expected=len(expected_items), predicted=len(predicted))
    unused = list(predicted)
    for exp in expected_items:
        label = exp["part_number"] or " ".join(exp["keywords"])
        hit = next((p for p in unused if _matches(exp, p)), None)
        if hit is None:
            s.errors.append(f"missed {label}")
            continue
        unused.remove(hit)
        s.matched += 1
        if hit.quantity == exp["quantity"]:
            s.quantity_ok += 1
        else:
            s.errors.append(f"{label}: quantity {hit.quantity}, expected {exp['quantity']}")
        if _same_brand(hit.brand, exp["brand"]):
            s.brand_ok += 1
        else:
            s.errors.append(f"{label}: brand {hit.brand!r}, expected {exp['brand']!r}")
        if _norm(hit.part_number) == _norm(exp["part_number"]):
            s.part_number_ok += 1
        else:
            s.errors.append(f"{label}: part_number {hit.part_number!r}, expected {exp['part_number']!r}")
    for extra in unused:
        s.errors.append(f"extra item {extra.part_number or extra.description!r}")
    return s


def ratio(a: int, b: int) -> float:
    return a / b if b else 1.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default=PROMPT_VERSION)
    parser.add_argument("--dataset", default="extraction", help="extraction (tuning set) or extraction_holdout")
    args = parser.parse_args()
    prompt, dataset = args.prompt, args.dataset

    cases = [json.loads(line) for line in (DATASETS / f"{dataset}.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    totals = CaseScore()
    rows, cost, ms, retries, crashed = [], 0.0, 0, 0, 0
    for case in cases:
        try:
            result = extract(case["text"], prompt_version=prompt)
        except Exception as e:  # noqa: BLE001 (a crash counts as a failed case)
            crashed += 1
            s = CaseScore(expected=len(case["expected"]), errors=[f"crashed: {e}"])
        else:
            s = score_case(case["expected"], result.rfq.line_items)
            cost += result.cost_usd
            ms += result.latency_ms
            retries += result.attempts - 1
        for name in ("expected", "predicted", "matched", "quantity_ok", "brand_ok", "part_number_ok"):
            setattr(totals, name, getattr(totals, name) + getattr(s, name))
        rows.append((case, s))
        print(f"{case['id']} {'PASS' if s.fully_correct else 'FAIL'}  {'; '.join(s.errors)}")

    precision = ratio(totals.matched, totals.predicted)
    recall = ratio(totals.matched, totals.expected)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    passed = sum(s.fully_correct for _, s in rows)
    metrics = [
        ("Cases fully correct", f"{passed}/{len(rows)} ({ratio(passed, len(rows)):.0%})"),
        ("Item precision", f"{precision:.1%}"),
        ("Item recall", f"{recall:.1%}"),
        ("Item F1", f"{f1:.1%}"),
        ("Quantity correct (matched items)", f"{ratio(totals.quantity_ok, totals.matched):.1%}"),
        ("Brand correct (matched items)", f"{ratio(totals.brand_ok, totals.matched):.1%}"),
        ("Part number correct (matched items)", f"{ratio(totals.part_number_ok, totals.matched):.1%}"),
        ("Retries needed", str(retries)),
        ("Crashes", str(crashed)),
        ("Total cost", f"${cost:.4f}"),
        ("Avg latency per case", f"{ms / max(len(rows) - crashed, 1):.0f} ms"),
    ]
    print()
    for name, value in metrics:
        print(f"{name:38} {value}")

    report = [f"# Extraction eval: `{prompt}`", "", f"Date: {date.today()} · Model: gpt-4o-mini · "
              f"Dataset: `{dataset}`, {len(cases)} cases, {totals.expected} line items", "", "| Metric | Value |", "|---|---|"]
    report += [f"| {n} | {v} |" for n, v in metrics]
    report += ["", "## Failures", ""]
    failures = [(c, s) for c, s in rows if not s.fully_correct]
    report += [f"- **{c['id']}** ({c['tag']}): {'; '.join(s.errors)}" for c, s in failures] or ["None."]
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / (f"{prompt}.md" if dataset == "extraction" else f"{prompt}-{dataset}.md")
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nreport -> {out}")


if __name__ == "__main__":
    main()
