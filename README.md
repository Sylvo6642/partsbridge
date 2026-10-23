# PartsBridge

A small marketplace for industrial spare parts, built to learn **AI engineering**.
Buyers paste a messy request, AI turns it into a matched parts list, sellers get an AI-drafted quote to check and send.

The web app is deliberately thin. The point is the AI layer: **structured outputs, tool calling, RAG, guardrails and
tracing**. Every AI feature has a test with a score.

> All data is synthetic: brands, sellers, prices and stock are made up. Part-number formats follow real conventions
> (a 6205 bearing has a 25 mm bore) so the matching problem is realistic.

## How it works
```
BUYER                                   SELLER
1. Paste a request (plain text)
2. AI pulls out the parts list
3. AI matches each part to the catalog
   (if unsure, the buyer picks one)
4. Publish                         ->   5. Inbox
                                        6. "Draft with AI" -> the AI fills in price + stock using tools
                                        7. The seller checks it and submits
8. See quotes, accept one          <-
```
One account has a Buyer / Seller switch, so a visitor can run the whole loop alone.

## The AI
| Feature | What it does | How it is scored |
|---|---|---|
| Extraction | Messy text → checked parts list (structured output) | Fields correct |
| Part matching | Search by part number + keyword + meaning (RAG), tools `search_catalog`, `find_equivalent`, confidence score | Right part in top 5 |
| Quoting | AI reads the buyer's notes (are substitutes allowed?); code applies the stock/substitution policy and prices every line. A tool-calling agent version is kept as the measured baseline | Lines and quotes correct, unwanted substitutions |
| Safety | AI never decides who sees what; injection tests; human clicks before sending; every AI call logged with cost | Attacks that succeed (target 0) |

Scores live in [`docs/evals/`](docs/evals/).

## Stack
Supabase (Postgres + pgvector + Auth) · OpenAI (gpt-4o-mini, text-embedding-3-small) · FastAPI · Next.js

## Roadmap
- [x] **Day 1:** repo, synthetic catalog (621 parts, 5 sellers, 1,321 offers), database schema, docs
- [x] **Day 2:** extraction (structured outputs + validation + retry), AI call logging, eval: 20/20 tuning, 9/10 held-out
- [x] **Day 3:** hybrid catalog search (part number + keyword + pgvector, merged with RRF): Recall@5 98% vs 85% best single method
- [x] **Day 4:** part-matching agent (tool calling, spec filter, code guardrails): held-out 83% correct vs 50% for search alone; confidently wrong 1 vs 6
- [x] **Day 5:** the app: login, per-visitor sandbox with Row Level Security enforced for API and agents, buyer screens that show the AI's work
- [x] **Day 6:** quoting + seller screens. The tool-calling agent scored 25% fully correct quotes; AI-reads-notes + code policy scored 100% at a tenth of the cost
- [ ] Day 7: bot seller + accept a quote (full loop); safety tests
- [ ] Day 8: deploy + check it as a brand-new visitor

Later, only if wanted: PDF upload, email input, photo input, tax/currency, a public stats page.

## Run it
```bash
cp .env.example .env            # fill in Supabase + OpenAI keys
cd backend
python -m venv .venv && .venv/Scripts/activate     # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.generate_catalog   # writes data/*.csv
python -m scripts.migrate            # creates the tables in Supabase
python -m scripts.load_catalog       # loads the catalog
python -m scripts.embed_catalog      # embeddings for search (~$0.001)
pytest
python -m scripts.smoke_buyer          # live check: buyer flow + isolation between two users (~$0.005)
python -m evals.run_extraction       # scores extraction (calls OpenAI, ~$0.003)
python -m evals.run_search           # scores each search method
python -m evals.run_matching         # scores the matching agent vs a no-AI baseline (~$0.03)
python -m evals.run_quoting --prompt quoting_v2   # scores quoting (v1 = the agent baseline)
python -m scripts.smoke_seller       # live check: seller flow + isolation
uvicorn app.main:app --port 8010     # API docs at http://127.0.0.1:8010/docs

cd ../frontend && npm install && npm run dev   # http://localhost:3000
```

## Docs
- [Decisions](docs/decisions.md): every choice and why
- [Journal](docs/journal/): one entry per build day
- [Demo walkthrough](docs/demo.md): what a visitor does
- [LinkedIn drafts](docs/linkedin/)
