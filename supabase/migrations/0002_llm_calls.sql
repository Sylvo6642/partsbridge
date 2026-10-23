-- Day 2: a log of every AI call: what it cost, how long it took, which prompt version produced it.

create table llm_calls (
  id              bigint generated always as identity primary key,
  created_at      timestamptz not null default now(),
  trace_id        uuid not null,               -- groups the calls made for one request
  user_id         uuid,                        -- who triggered it (from Day 5)
  feature         text not null,               -- 'extraction', 'matching', 'quoting'
  prompt_version  text not null,               -- e.g. 'extraction_v1'
  model           text not null,
  input_tokens    integer not null default 0,
  output_tokens   integer not null default 0,
  cost_usd        numeric(12, 6) not null default 0,
  latency_ms      integer not null,
  ok              boolean not null,
  error           text
);

create index llm_calls_created_at_idx on llm_calls (created_at desc);

-- Internal only: RLS on, no policy, so only the backend can read it.
alter table llm_calls enable row level security;
