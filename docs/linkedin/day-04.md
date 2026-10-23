# PartsBridge, Day 4 (draft)

## Hook options
1. My first AI agent was 100% safe and completely useless.
2. The biggest jump in my agent's accuracy didn't come from the prompt.
3. Search alone picked the wrong part 19 times. My agent: 0.

## Post
PartsBridge, Day 4.

Today I built my first agent. It takes one line from a buyer's request and finds the part in the catalog.

It can search, filter by specs, then decide:
Matched. Ask the buyer. Or not in the catalog.

Tested on 32 lines. The number I care most about: how often it picks the wrong part with confidence. That's the mistake that costs a buyer money.

Search alone (take the #1 result): 41% correct. 19 wrong picks.

Agent v1: 0 wrong picks. 38% correct.
It asked the buyer about everything. My search tool returned the same bearing from 3 brands as 3 rows. The model thought they were 3 different parts.

v2: grouped brands under one part. 66%. Half the cost.

v3: gave it a filter tool. The model fills in specs (bore 40, sealed). Postgres compares the numbers. 81%.

v4: moved brand choice into plain code. 88%. 0 wrong picks.

On 12 new lines it never saw: 83% vs 50% for search alone.

What I learned today:
→ Tool output shape matters as much as the prompt.
→ Small models are bad at comparing numbers. Databases aren't. Let each do its job.
→ If it's a fixed rule, write code, not a prompt.
→ "I'm not sure, please pick" is a good answer. A confident wrong one isn't.

Still 1 wrong pick in the new set: 18.5 kW asked, 11 kW matched. That's why the buyer confirms every match.

I'm using AI to help build this. I make the calls and I understand every line before it goes in.

Day 5: the app. Sign up, paste a request, watch the AI work.

## First comment
Repo, agent code and every eval version: https://github.com/Sylvo6642/partsbridge
