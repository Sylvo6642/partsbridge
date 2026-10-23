"""Score the matching agent (and a no-AI baseline) on labelled buyer lines.

Run from backend/:  python -m evals.run_matching [--prompt matching_v4] [--dataset matching_holdout]

Each case expects one of:
- matched:       the chosen part is in the right interchange group (and the right brand, if one is expected)
- needs_choice:  the agent asks the buyer (we also report how many of the right options it offered)
- not_found:     the agent says the catalog doesn't have it

"Confidently wrong" = the agent said "matched" but the part is wrong, or it should have asked / said not found.
That is the costly mistake: a buyer would get quotes for the wrong part.
Baseline = take hybrid search's #1 result and always call it a match (no AI decisions).
"""

import argparse
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from app.ai.extraction import LineItem
from app.ai.matching import agent, search
from app.db import connect

DATASETS = Path(__file__).parent / "datasets"
REPORTS = Path(__file__).resolve().parents[2] / "docs" / "evals"


def load_parts() -> dict[int, tuple[str, str, str]]:
    with connect() as conn:
        return {r[0]: (r[1], r[2], r[3]) for r in
                conn.execute("select id, interchange_group, brand, part_number from parts")}


def judge(expected: dict, status: str, part_id: int | None, candidates: list[int], parts) -> tuple[bool, bool, str]:
    """Returns (correct, confidently_wrong, note)."""
    if status == "matched":
        group, brand, pn = parts.get(part_id, ("?", "?", "?"))
        if expected["status"] != "matched":
            return False, True, f"picked {brand} {pn} but should be {expected['status']}"
        if group not in expected["groups"]:
            return False, True, f"picked {brand} {pn} ({group}), wrong part"
        if expected["brand"] and brand != expected["brand"]:
            return False, True, f"picked {brand} {pn}, wanted brand {expected['brand']}"
        return True, False, ""
    if status != expected["status"]:
        return False, False, f"said {status}, expected {expected['status']}"
    return True, False, ""


def coverage(expected: dict, candidates: list[int], parts) -> float | None:
    if expected["status"] != "needs_choice":
        return None
    offered = {parts[c][0] for c in candidates if c in parts}
    return len(offered & set(expected["groups"])) / len(expected["groups"])


def run_case(case: dict, prompt: str) -> dict:
    line = LineItem(**case["line"])
    query = f"{line.part_number or ''} {line.description}".strip()
    with connect() as conn:
        top = search.hybrid(conn, query, line.part_number, limit=1)
        result = agent.match_line(conn, line, prompt_version=prompt)
    return {"case": case, "baseline_part": top[0].part_id if top else None, "result": result}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default=agent.PROMPT_VERSION)
    parser.add_argument("--dataset", default="matching", help="matching (tuning set) or matching_holdout")
    args = parser.parse_args()
    prompt, dataset = args.prompt, args.dataset

    parts = load_parts()
    cases = [json.loads(line) for line in (DATASETS / f"{dataset}.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    with ThreadPoolExecutor(max_workers=6) as pool:
        runs = list(pool.map(lambda c: run_case(c, prompt), cases))

    by_tag = defaultdict(lambda: {"n": 0, "agent": 0, "baseline": 0})
    agent_ok = base_ok = agent_wrong = base_wrong = guardrails = 0
    covs, notes = [], []
    calls = tools = cost = ms = 0
    for run in runs:
        case, r = run["case"], run["result"]
        d = r.decision
        ok, wrong, note = judge(case["expected"], d.status, d.part_id, d.candidate_part_ids, parts)
        b_ok, b_wrong, _ = judge(case["expected"], "matched" if run["baseline_part"] else "not_found",
                                 run["baseline_part"], [], parts)
        cov = coverage(case["expected"], d.candidate_part_ids, parts)
        if cov is not None and d.status == "needs_choice":
            covs.append(cov)
        agent_ok += ok; base_ok += b_ok; agent_wrong += wrong; base_wrong += b_wrong
        guardrails += r.guardrail is not None
        calls += r.model_calls; tools += len(r.tool_calls); cost += r.cost_usd; ms += r.latency_ms
        t = by_tag[case["tag"]]; t["n"] += 1; t["agent"] += ok; t["baseline"] += b_ok
        status = "PASS" if ok else ("WRONG" if wrong else "FAIL")
        print(f"{case['id']} {status:5} {d.status:12} {note} {('[guardrail: ' + r.guardrail + ']') if r.guardrail else ''}")
        if not ok:
            notes.append(f"- **{case['id']}** ({case['tag']}) `{case['line']['part_number'] or ''} "
                         f"{case['line']['description']}`: {note}. Agent's reason: {d.reason}")

    n = len(runs)
    lines = [f"# Matching eval: `{prompt}`", "",
             f"Date: {date.today()} · dataset `{dataset}` · {n} buyer lines · model gpt-4o-mini · max {agent.MAX_TURNS} model calls per line",
             "", "| Metric | Baseline (search #1) | Agent |", "|---|---|---|",
             f"| Correct decision | {base_ok}/{n} ({base_ok / n:.0%}) | {agent_ok}/{n} ({agent_ok / n:.0%}) |",
             f"| **Confidently wrong** (lower is better) | {base_wrong} | {agent_wrong} |",
             f"| Right options offered when asking | n/a | {sum(covs) / len(covs):.0%} |" if covs else
             "| Right options offered when asking | n/a | n/a |",
             f"| Guardrail overrides | n/a | {guardrails} |",
             f"| Model calls per line (avg) | 0 | {calls / n:.1f} |",
             f"| Tool calls per line (avg) | 0 | {tools / n:.1f} |",
             f"| Cost per line (avg) | ~$0.000001 | ${cost / n:.5f} |",
             f"| Latency per line (avg) | <0.5 s | {ms / n / 1000:.1f} s |",
             "", "## By line type", "", "| Type | n | Baseline | Agent |", "|---|---|---|---|"]
    lines += [f"| {tag} | {t['n']} | {t['baseline']}/{t['n']} | {t['agent']}/{t['n']} |" for tag, t in by_tag.items()]
    lines += ["", "## Agent mistakes", ""] + (notes or ["None."])
    report = "\n".join(lines) + "\n"
    print("\n" + report)
    (REPORTS / (f"{prompt}.md" if dataset == "matching" else f"{prompt}-{dataset}.md")).write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
