# PartsBridge, Day 1 (draft)

## Hook options
1. The same bearing has three part numbers. That's the whole AI problem I'm building for.
2. Day 1 of my third AI project and I didn't call a single model. On purpose.
3. 621 parts, 5 sellers, 0 real data. Day 1 of PartsBridge.

## Post
PartsBridge, Day 1.

New project. A small marketplace for industrial spare parts. Buyers paste a messy request, AI turns it into a matched
parts list, sellers get an AI-drafted quote to check and send.

The app stays thin. The AI is the point. Every AI feature gets a test and a score.

Today was setup. No AI yet.

Built a generator for fake catalog data. 621 parts. Bearings, belts, filters, motors. 3 made-up brands. 5 sellers.

But the part-number rules are real. Same bearing, three brands:
6205-2RS1. 6205DDU. 6205-2RSR.
A buyer might type any of them. Or "6205 2rs". Or "sealed bearing 25mm shaft".

That's what the AI has to solve. If the fake data is too clean, there's nothing to test.

What I learned today:
→ Normalize part numbers first. "6205-2RS1" and "6205 2rs1" become the same string. Cheapest search there is.
→ Fixed random seed = same data every run = scores I can compare across days.
→ Row Level Security on from day one. No rule means no access.
→ Money is never a float.

I'm using AI to help build this. I make the calls and I understand every line before it goes in.

Day 2: extraction. Messy text in, checked parts list out, first score.

## First comment
Repo and day-by-day journal: https://github.com/Sylvo6642/partsbridge
