# PartsBridge, Day 2 (draft)

## Hook options
1. My prompt scored 100%. Then I tested it on messages it had never seen.
2. I fixed 5 bugs in my prompt and created 4 new ones. The eval caught it in 40 seconds.
3. Day 2: the AI reads messy buyer emails. Here's what it got wrong.

## Post
PartsBridge, Day 2.

Today the AI reads messy buyer messages and turns them into a clean parts list.

"a dozen 6204ZZ and a pair of B60 belts" becomes:
6204ZZ, qty 12. B60, qty 2.

Built it with structured outputs. The model has to answer in a fixed shape. Plain code checks the answer. If something is off, it retries once and is told what was wrong.

Then I wrote 20 test messages with the right answers. Emails, tables, typos, German, one prompt injection.

Prompt v1: 15/20.
It put "A42 V-belt" in the part number field. It hid a whole part inside the notes.

Prompt v2: fixed all of that. And broke 4 messages that used to pass.
My own example taught it that "DDU" in 6205DDU was just a word.

Prompt v3: 20/20.

Then I wrote 10 new messages and never tuned the prompt on them. v3 got 9/10.

What I learned today:
→ Structured output guarantees the shape, not the meaning. You still need checks.
→ Every prompt change can break something. Without a test set you won't see it.
→ A perfect score on the set you tuned on means very little. Keep a held-out set.
→ Log every AI call. 102 calls today cost $0.014 total.

I'm using AI to help build this. I make the calls and I understand every line before it goes in.

Day 3: searching the catalog. Keywords plus meaning.

## First comment
Repo, prompts, test sets and eval reports: https://github.com/Sylvo6642/partsbridge
