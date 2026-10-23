# PartsBridge, Day 3 (draft)

## Hook options
1. "Open (no seals)" broke my search. Two words.
2. Keyword search: 85%. Vector search: 85%. Both together: 98%.
3. I embedded my whole catalog for $0.0006. The hard part was everything else.

## Post
PartsBridge, Day 3.

Today: search. A buyer asks for a part, find it in the catalog.

Built three ways to search:
Exact part number. Keyword search in Postgres. Meaning search with embeddings in pgvector.

Then merged them with Reciprocal Rank Fusion. Each method ranks the parts. A part that shows up high in several lists wins.

Tested on 40 queries. Codes, messy codes, plain descriptions, different words for the same thing.

Part number only: 42%.
Keyword: 78%.
Meaning: 88%.
All three combined: 92%.

Then I read the misses.

"6205 sealed bearing" returned the open bearing first. Why? Its description said "open (no seals)". Keyword search turns "seals" and "sealed" into the same word. Embeddings don't care much about "no" either.

And "1.5 kW" was split into "1" and "5". My bug.

Fixed both. Combined search: 98%.

What I learned today:
→ No single search method wins. They fail on different queries.
→ RRF only needs ranks. No need to compare scores from different systems.
→ Negation in your documents hurts keyword and vector search.
→ Search finds candidates. It doesn't check that the size is right. That's tomorrow's job.

I'm using AI to help build this. I make the calls and I understand every line before it goes in.

Day 4: an agent that checks the candidates, picks one, or asks the buyer.

## First comment
Repo, search code and eval reports: https://github.com/Sylvo6642/partsbridge
