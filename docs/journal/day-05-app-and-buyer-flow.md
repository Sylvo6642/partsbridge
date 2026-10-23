# Day 5: the app, login, and the buyer flow

## What I built
**Backend**
- Migration `0004`: `rfqs`, `rfq_lines`, `quotes`, `quote_lines`. Every row has a `workspace_id` (= the user), and
  every table has a Row Level Security policy `workspace_id = auth.uid()`. Each visitor also gets their own seller shop.
- `app/auth.py`: verifies the Supabase login token (ES256, public keys from Supabase's JWKS endpoint). Sign-up goes
  through the backend, which creates an already-confirmed account (no email round trip) and seeds the sandbox: the
  visitor's shop, stocked from a bot seller's price list, plus 3 sample RFQs from bot buyers.
- `app/db.py → as_user(user_id)`: every request runs inside a transaction that switches to Supabase's
  `authenticated` role with the user's id, so **Postgres enforces RLS on every query the API and the AI agents run**.
- `app/ai/pipeline.py`: extraction, then one matching agent per line **in parallel** (5 threads).
- Buyer API: analyze, list, detail, pick a part / change quantity / remove a line, publish.
- Migration `0005`: the RFQ stores the AI trace id, so the API can summarize the AI's work (calls, tokens, time, cost)
  straight from the `llm_calls` log.

**Frontend** (Next.js 16, Tailwind 4, designed with the impeccable skill)
- Product record in `PRODUCT.md`; design direction "printed industrial parts catalog" chosen by Kevin, in the
  surface brief at `.impeccable/surfaces/frontend.md`.
- Sign up / sign in, My requests, New request (with progress through the 3 AI steps), and the review page.
- The review page is the heart of it. Each line is a catalog row: an edge tab for the category, the buyer's words,
  the matched part (bold part number, brand, spec line) and the AI's decision with its one-line reason. When the
  agent asks the buyer to choose, the options appear as catalog rows **with the specs that differ highlighted**, so
  the buyer sees exactly what their request didn't say. A footer shows the real AI trace:
  "10 AI calls (1 extraction, 9 matching) · 19.9 s model time · $0.0031".

## Concepts, in plain words

**Authentication vs authorization.** Authentication = who are you (the login token, checked against Supabase's
public key). Authorization = what may you see. Here authorization lives in the database: RLS policies filter every
row by `auth.uid()`. The API never builds "where user_id = …" filters by hand, and the AI never decides anything
about access.

**Why `set local role authenticated`?** The backend's database user is an admin that skips RLS. For each request we
open a transaction, switch to the restricted role and set the user id. Postgres then applies the same rules it would
apply to the browser. The system connection is kept for system jobs (seeding, logs, bots).

**Parallel agents.** A request with 3 lines runs 3 matching agents at the same time, each with its own database
connection (also running as the user). Wall time is roughly the slowest line instead of the sum.

## Things the browser test caught
- **Next.js 16 Cache Components:** reading the URL (`usePathname`) in the shell outside a `<Suspense>` boundary blocks
  prerendering, and wrapping the whole page in Suspense made Next skip validating it. Fix: only the header (which
  reads the URL) streams in behind a static blue bar, and the page renders normally.
- **The agent listed brands of one motor as separate options** ("2.2 kW motor": 3 brands of the B3 motor + the B5
  one). The prompt says "one option per physical part", but the model ignored it. Fixed in plain code (`settle_brand`
  now keeps one option per physical part), same lesson as Day 4.
- Column widths jumped when a line changed state; the table now has fixed column widths.

## Verified
- `scripts/smoke_buyer.py` (live): two throwaway users. User A pastes a request, and 3/3 lines matched for $0.002.
  User B gets **404** for A's RFQ and an empty list; no token gets **401**. Both users are deleted afterwards.
- In the browser: sign up → paste the "vague on purpose" example → 3 lines, all "Choose one" with highlighted differences →
  picked an option → brand selector and counters update. No console errors.
- 21/21 unit tests, TypeScript and ESLint clean.

## Next (Day 6)
The seller side: the quote agent (tools `get_stock`, `get_price`, `compute_total`, `find_equivalent`), the seller
inbox, and the quote editor where a person approves the AI's draft.
