# Day 4: the part-matching agent

## What I built
- `app/ai/matching/agent.py`: **an agent loop**. The model gets one buyer line and some tools. It calls tools,
  reads the results, maybe calls more, and then gives a decision: `matched` (with a part), `needs_choice` (with
  options for the buyer) or `not_found`. At most 5 model calls per line.
- `app/ai/matching/tools.py`: the tools, in four versions (each one is in the eval history):
  `search_catalog` (Day 3's hybrid search), `find_equivalent`, and `filter_catalog` (exact spec filter in Postgres).
- **Guardrails in plain code:**
  - the agent may only choose a part a tool actually returned (`check_decision`)
  - code, not the model, picks the brand (`settle_brand`)
  - tools have no user, seller or workspace arguments, so the model can't choose whose data is read (a test checks this)
- An eval of 32 tuning lines + 12 held-out lines, comparing the agent with a no-AI baseline ("take search's #1").

## Concepts, in plain words

**Tool calling.** We describe each tool to the model with a name, a sentence and a JSON schema for its arguments.
The model doesn't run anything. It replies "please call `filter_catalog` with category=motor, power_kw=1.5".
Our code runs it and sends back the result. The model never touches the database.

**The agent loop.** Repeat: ask the model → if it wants tools, run them and append the results → ask again. Stop
when it answers or after 5 rounds. The limit keeps cost and latency bounded, even if the model goes in circles.

**Abstaining.** "I'm not sure, please choose" is a good answer when the buyer left something out. The expensive
mistake is a *confident wrong match*: the buyer gets quotes for the wrong part. So that's the headline metric.

## The version story (32 tuning lines)

| Version | What changed | Correct | Confidently wrong | Cost per line |
|---|---|---|---|---|
| Baseline | No AI: search's #1 result, always "matched" | 41% | **19** | ~$0 |
| v1 | Agent + `search_catalog` (one row per brand) + `find_equivalent` | 38% | 0 | $0.00093 |
| v2 | Search returns **one result per physical part**, brands listed under it | 66% | 0 | $0.00050 |
| v3 | + `filter_catalog`: the model fills in specs, Postgres compares numbers exactly | 81% | 1 | $0.00091 |
| v4 | + code picks the brand, the prompt says what the catalog sells | 84% → **88%** after a bug fix | **0** | $0.00078 |

**Held-out (12 lines written after v4, never tuned on): agent 83% with 1 confidently wrong, baseline 50% with 6.**

What each step taught me:
- **v1 was safe but useless.** It saw `6205-2RS1`, `6205DDU`, `6205-2RSR` as three parts and asked the buyer to
  choose every time. The problem was **my tool's output shape**, not the prompt.
- **v2: design tool output for the model.** Grouping brands under the physical part fixed most of that and *halved*
  the cost (fewer calls).
- **v3: let code do what code is good at.** gpt-4o-mini is bad at comparing "40 × 90 × 23" against a list of specs.
  With `filter_catalog`, the model only turns words into fields (`bore_mm=40, outer_diameter_mm=90, ...`), and
  the database compares the numbers. That was the biggest jump.
- **v4: don't ask a model to apply a fixed rule.** Picking the brand ("the one the buyer named, else the one whose
  part number they wrote") is a fixed rule, so it's code now. My first version of that code had a bug: `A-42` (Kanto)
  and `A42` (Norvik) are identical once normalized, so it picked the wrong one. Fixed by comparing the exact text first.

## Known issues (honest list)
- **18.5 kW motor → matched to an 11 kW motor** (held-out h12). The model's own reason says "18.5 kW is not
  available", yet it said "matched". This is why the buyer confirms every match in the app (Day 5).
- For parts we don't sell ("SPZ belt", "15 kW motor"), the agent often offers close alternatives instead of saying
  "not found". That's not dangerous (the buyer chooses), but it's scored as wrong.
- Results vary a little between runs, even at temperature 0. One line can flip from run to run.
- I tuned on the 32 lines, so 88% is optimistic. 83% on the held-out lines is the honest number, and 12 lines is
  a small sample.

## Numbers
- Agent v4: tuning 88% / 0 confidently wrong; held-out 83% / 1 confidently wrong
- About 2.7 model calls, 1.7 tool calls, **$0.0008** and ~4 s per line
- All OpenAI spend on the project so far: $0.16 (most of it from running these evals)
- 21/21 unit tests pass

## Next (Day 5)
The app: sign up / log in, a sandbox for each visitor, the buyer screens (paste → extract → match → confirm →
publish), and the AI wired into it.
