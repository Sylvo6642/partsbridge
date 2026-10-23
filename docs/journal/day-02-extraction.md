# Day 2: extraction, and the first score

## What I built
- `app/ai/llm.py`: **the one place that calls OpenAI.** It asks for structured output, times the call, prices it
  and logs it.
- `llm_calls` table (migration `0002`): every AI call with its prompt version, tokens, cost (USD), latency, and
  success or error.
- `app/ai/extraction.py`: a messy message becomes `ExtractedRFQ{line_items[part_number, brand, description, quantity],
  needed_by, notes}`. Plain-code checks run after the model; if something is wrong, it retries once and tells the
  model what was wrong.
- Prompts live in files with versions: `prompts/extraction_v1.md`, `v2`, `v3`.
- **Eval:** 20 labelled messages for tuning + 10 held-out messages, and a scorer (`evals/run_extraction.py`).
- A small FastAPI server: `/health`, `/parts?part_number=`, `/extract`.

## Concepts, in plain words

**Structured output.** Instead of asking for "JSON please" and hoping, we hand the model a Pydantic class.
OpenAI forces the answer to fit that shape, so we always get the fields we need with the right types. That
guarantees the *shape*, not the *meaning*: the model can still put "A42 V-belt" in the part-number field.
That's why the plain-code checks and the eval exist.

**Validate, then retry with feedback.** `problems()` is ordinary code (quantity ≥ 1, description not empty). If it
finds something, the second attempt includes "your previous answer had these problems". Retries needed in all
runs so far: 0. The safety net is there, and the eval shows when it gets used.

**Eval = a labelled test set + a number.** Each message has a hand-written right answer. The scorer pairs up
predicted and expected items and reports precision (how many predictions were real), recall (how many real items
were found), F1, and per-field accuracy.

**Tuning set vs held-out set.** I wrote v2 and v3 while looking at the 20 tuning messages, so a score on those is
too optimistic. The 10 held-out messages were written afterwards and never used to change the prompt. That's
the honest number.

## The prompt story (with numbers)

| Prompt | What changed | Tuning set (20) | Held-out (10) |
|---|---|---|---|
| v1 | Plain instructions | 15/20 (F1 85.7%) | 10/10 |
| v2 | "Only the code in part_number" + examples; "never put parts in notes"; brand next to the part number | 16/20 (F1 87.5%) | not run |
| v3 | v2 + "suffixes like DDU, 2RS, -2RSR are part of the code" | **20/20 (F1 100%)** | 9/10 |

- **v1 failures:** description words inside the part number (`A42 V-belt`, `6310 open`, `Keilriemen SPA1250`). It
  also put a whole requested part into `notes` ("any brand ok for SPB1500 x3").
- **v2 fixed those, and broke 4 others.** My example `"6310 open" -> "6310"` taught the model that letters after
  the number are words, so `6205DDU` became `6205`. Without the eval I would never have seen this regression.
- **v3** says suffixes are part of the code. 20/20 on the tuning set.
- **Held-out:** v3 got 9/10. It read the thread size `3/4-16` as a part number, a new kind of mistake caused by the
  "only the code" rule. v1 got 10/10 on these, but its 10 messages are easier than the tuning set.

**Decision (D-016):** keep v3, which scores 29/30 overall against v1's 25/30. The `3/4-16` case is a known issue. I won't tune
on the held-out set, or it stops being a fair test.

**Lesson:** a perfect score on the set you tuned on means very little. 10 held-out cases is small, too: one case
is 10 percentage points.

## Something for Day 4
Live test: "10x 6205 sealed bearings" → `part_number: "6205"`, `description: "sealed bearing"`. That's a correct
extraction. But an exact lookup of `6205` finds the **open** bearing. The matcher must read the description too
("sealed" → `2RS` group), not just the part number.

## Numbers
- Extraction v3: tuning 20/20, held-out 9/10, quantities 100% correct, 0 retries, 0 crashes
- Cost: about **$0.00015 per message**. All of today's eval runs (102 calls) cost **$0.014** in total
- Latency: ~1.7–2.0 s per message (gpt-4o-mini)
- 11/11 unit tests pass

## Next (Day 3)
Catalog search: keyword search (Postgres full-text) + meaning search (embeddings in pgvector), combined, and a test:
is the right part in the top 5?
