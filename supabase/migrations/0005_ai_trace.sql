-- Link app rows to the AI calls that produced them, so the UI can show the AI's work (calls, time, cost).
alter table rfqs   add column ai_trace_id uuid;
alter table quotes add column ai_trace_id uuid;
create index llm_calls_trace_idx on llm_calls (trace_id);
