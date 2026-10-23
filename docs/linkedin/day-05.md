# PartsBridge, Day 5 (draft)

## Hook options
1. My AI agent doesn't decide who sees what. The database does.
2. Day 5: the AI got a face. Here's how I made it show its work.
3. "Choose one" is a feature, not a failure.

## Post
PartsBridge, Day 5.

Today the AI got an app around it. Sign up, paste a parts request, check what the AI matched, publish.

The backend part I care about most: security.

Every row has an owner. Postgres Row Level Security filters every query by the logged-in user. The API switches into that user's role for each request. The AI agents run inside it too.

So the model never decides who sees what. Even if a prompt injection tricks it, the database won't hand over another user's rows.

Tested it with two throwaway users. User B asks for User A's request: 404.

The frontend part I care about most: showing the AI's work.
Every line shows the match, the AI's one-line reason, and its status.
When it's not sure, it shows the options. The specs that differ are highlighted. "25mm shaft" fits 3 bearings. Different outer diameters. Now you can see why it asked.
The footer shows the real trace: 10 AI calls, 19.9 s, $0.0031.

What I learned today:
→ Authorization belongs in the database, not in prompts.
→ Run agents in parallel. 3 lines take as long as the slowest one.
→ Showing the reason and the options builds more trust than a confident answer.
→ Test in a real browser. It found a bug the evals missed: the agent listed brands of one motor as separate options. Fixed in code.

I'm using AI to help build this. I make the calls and I understand every line before it goes in.

Day 6: the seller side. An AI drafts the quote, a person approves it.

## First comment
Repo and day-by-day journal: https://github.com/Sylvo6642/partsbridge
