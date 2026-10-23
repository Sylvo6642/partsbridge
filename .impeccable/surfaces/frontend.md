---
version: 1
slug: "frontend"
primary_target: "frontend"
related_targets: []
---

# Surface brief: PartsBridge web app (all screens)

Scope: the whole frontend in `frontend/` (login, buyer requests, new request review, request detail with quotes,
seller inbox, seller quote editor). Visitor mode: **Operate**. Build path: code-led (no image generation).

Audience and job: portfolio visitors trying both roles alone, and the simulated buyer/seller. Success: a first-time
visitor pastes a request, understands what the AI matched and why, fixes what's flagged, publishes, quotes, accepts.
Constraints: AI steps take seconds (show progress); money exact; no on-screen synthetic-data disclaimer.

## Direction contract

THESIS: The app reads like a well-made printed industrial parts catalog: every part is a spec row with real
dimensions and a bold part number, categories carry edge thumb tabs. It refuses the grey SaaS card dashboard and
the "AI chat" look; the AI shows up as status, reason and options inside catalog rows.

OWN-WORLD: White paper ground, carbon ink text, one catalog blue (cover blue) for the top bar, primary actions,
links and selection. Light grey table banding and hairline rules. Four muted category tab colours (bearing, belt,
filter, motor) used only on the edge tabs. State colours only for match status (matched green, choose amber,
not found red), always with a glyph. Archivo throughout, with its condensed width for part numbers and tab
labels; tabular figures for every number. A tight 3-size type scale, rank by weight and case.

STORY: The visitor pastes a messy request, watches three AI steps, reads a catalog table of what was matched and why,
picks options where flagged, publishes, then sees quotes compared line by line on one baseline and accepts one.
As seller: opens a request, drafts a quote with AI, edits prices or quantities, submits.

FIRST VIEWPORT: Catalog-blue top bar: wordmark left, role nav (Buyer: My requests, New request; Seller: Inbox)
centre-left, Buyer/Seller segmented switch and account right. New request: wide paste area with a sample-request
helper and the primary "Analyze with AI" button; beside it a short three-step explainer. After analysis the lines
table takes the full width: edge tab, qty, the buyer's words, the matched part (big part number, brand, spec
line), status with the agent's reason. A sticky footer holds the AI trace (calls, time, cost) and Publish.

FORM: Pick card (the printed industrial parts catalog), candidate 1 of 7 on my ordered list. seed:103d3fd15673ead9.
Signature move: catalog spec rows with edge thumb tabs; on a "choose" line, the options are shown as catalog rows
where the specs that differ are highlighted, so the missing information is visible at a glance. Motion: the
three-step AI progress, and a short settle when an option is chosen. Nothing else animates.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
