# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Next.js (App Router) + TypeScript + Tailwind CSS in `frontend/`, talking to the FastAPI backend in `backend/`
(Bearer token from Supabase Auth via supabase-js). Decided in the project plan (D-003, D-007).

## Users

Two audiences, balanced (confirmed 2026-10-23):
- **Portfolio visitors** (recruiters, hiring managers, engineers) who sign up and try the demo alone in a few
  minutes. They should see what the AI did and why.
- **The roles the app simulates**: a maintenance or procurement **buyer** who pastes a messy parts request and
  needs a correct, quotable parts list; a **seller** at an industrial distributor who answers RFQs with a quote.
  The app should read as a realistic tool for them, with the AI layer visible but not shouting.

## Product Purpose

PartsBridge is an RFQ marketplace for industrial spare parts (bearings, V-belts, filters, motors). A buyer pastes
a request, AI extracts the parts list and matches each line to the catalog (or asks the buyer when it's unsure),
the buyer publishes it, sellers answer with AI-drafted quotes that a human checks, and the buyer accepts one.
It exists as an AI-engineering portfolio project: the web app is deliberately thin; the value is the AI layer
(structured outputs, tool-calling agents, hybrid RAG, guardrails, tracing), each feature with a measured eval score.

## Positioning

Every AI decision is shown with its evidence: match status (matched / needs your choice / not found), the agent's
one-line reason, the options it considered, and what the step cost. The AI suggests; people confirm; code
enforces prices and permissions. A visitor can run the whole buyer-to-seller loop alone (Buyer/Seller switch,
bot buyers and bot sellers).

## Operating Context

- One account, two roles via a Buyer/Seller switch. Each visitor has a private sandbox workspace.
- Buyer flow: paste request → AI analysis (~3–10 s) → review lines, pick options, edit quantities, remove lines →
  publish → quotes arrive from bot sellers → accept one.
- Seller flow: inbox of published RFQs (three sample RFQs from bot buyers at signup, plus the visitor's own) →
  "Draft with AI" → editable quote lines (part, qty, unit price, line total, stock, lead time, note) → submit.
- Domain vocabulary: RFQ, line, part number, brand, interchangeable part, lead time, stock, quote, accept.

## Capabilities and Constraints

- Catalog: 621 parts, 3 fictional brands (Norvik, Kanto Seiko, Ferrum), 5 bot sellers, prices in USD.
- AI calls take seconds; the UI must show progress and never look frozen.
- Money is exact (2 decimals); prices come from the database, never from the model.
- No on-screen "synthetic data" disclaimer (decided 2026-10-23); disclosure lives in the README.

## Brand Commitments

Name: **PartsBridge**. No existing logo, palette or type. Must be clean and aesthetic (Kevin, 2026-10-23).
All frontend design and review uses the impeccable skill.

## Evidence on Hand

Eval scores in `docs/evals/` (extraction, search, matching) are real measured numbers. There are no real customers,
testimonials, logos or usage numbers; never fabricate them.

## Product Principles

1. Show the AI's work: status, reason and options, never a bare answer.
2. People confirm; the AI never commits anything on its own.
3. Calm and precise over flashy: this is a tool people would use at work.
4. Every screen works for someone who has never seen the app before.
