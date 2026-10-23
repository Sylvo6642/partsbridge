-- Day 5: the app. Every app row belongs to a workspace = the user who owns it.
-- Row Level Security makes the database itself refuse rows from other workspaces,
-- so even a bug in the API (or a tricked AI) can't read another visitor's data.

-- Each visitor gets their own seller shop; bot sellers have no owner.
alter table sellers add column owner_id uuid references auth.users (id) on delete cascade;
create sequence sellers_id_seq start 1000 owned by sellers.id;
alter table sellers alter column id set default nextval('sellers_id_seq');

drop policy "sellers are public" on sellers;
create policy "bot sellers and your own shop" on sellers for select
  using (owner_id is null or owner_id = auth.uid());
create policy "your own shop's offers" on offers for select
  using (exists (select 1 from sellers s where s.id = offers.seller_id and s.owner_id = auth.uid()));

create table rfqs (
  id            uuid primary key default gen_random_uuid(),
  workspace_id  uuid not null default auth.uid() references auth.users (id) on delete cascade,
  buyer_name    text not null,                    -- 'You', or a bot buyer's company for sample RFQs
  is_sample     boolean not null default false,   -- made by a bot buyer for the visitor to quote on
  raw_text      text not null,                    -- what the buyer pasted
  needed_by     text,
  notes         text,
  status        text not null default 'draft' check (status in ('draft', 'published', 'awarded')),
  created_at    timestamptz not null default now(),
  published_at  timestamptz
);

create table rfq_lines (
  id                  uuid primary key default gen_random_uuid(),
  rfq_id              uuid not null references rfqs (id) on delete cascade,
  workspace_id        uuid not null default auth.uid() references auth.users (id) on delete cascade,
  line_no             integer not null,
  part_number_raw     text,
  brand_raw           text,
  description         text not null,
  quantity            integer not null check (quantity > 0),
  match_status        text not null check (match_status in ('matched', 'needs_choice', 'not_found')),
  match_reason        text,
  suggested_part_ids  bigint[] not null default '{}',   -- the AI's match, or the options it offered
  part_id             bigint references parts (id)      -- the part the buyer settled on
);

create table quotes (
  id              uuid primary key default gen_random_uuid(),
  rfq_id          uuid not null references rfqs (id) on delete cascade,
  workspace_id    uuid not null default auth.uid() references auth.users (id) on delete cascade,
  seller_id       bigint not null references sellers (id),
  status          text not null default 'draft' check (status in ('draft', 'submitted', 'accepted', 'rejected')),
  subtotal        numeric(12, 2),
  shipping        numeric(12, 2),
  total           numeric(12, 2),
  lead_time_days  integer,
  notes           text,
  created_at      timestamptz not null default now(),
  submitted_at    timestamptz,
  unique (rfq_id, seller_id)
);

create table quote_lines (
  id              uuid primary key default gen_random_uuid(),
  quote_id        uuid not null references quotes (id) on delete cascade,
  workspace_id    uuid not null default auth.uid() references auth.users (id) on delete cascade,
  rfq_line_id     uuid not null references rfq_lines (id) on delete cascade,
  part_id         bigint references parts (id),          -- null = the seller can't supply this line
  quantity        integer not null check (quantity >= 0),
  unit_price      numeric(12, 2),
  line_total      numeric(12, 2),
  lead_time_days  integer,
  note            text
);

create index rfq_lines_rfq_idx on rfq_lines (rfq_id);
create index quotes_rfq_idx on quotes (rfq_id);
create index quote_lines_quote_idx on quote_lines (quote_id);

alter table rfqs        enable row level security;
alter table rfq_lines   enable row level security;
alter table quotes      enable row level security;
alter table quote_lines enable row level security;

create policy "own workspace" on rfqs        for all using (workspace_id = auth.uid()) with check (workspace_id = auth.uid());
create policy "own workspace" on rfq_lines   for all using (workspace_id = auth.uid()) with check (workspace_id = auth.uid());
create policy "own workspace" on quotes      for all using (workspace_id = auth.uid()) with check (workspace_id = auth.uid());
create policy "own workspace" on quote_lines for all using (workspace_id = auth.uid()) with check (workspace_id = auth.uid());

grant select, insert, update, delete on rfqs, rfq_lines, quotes, quote_lines to authenticated;
grant select on parts, sellers, offers to authenticated;
