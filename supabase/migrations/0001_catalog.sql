-- Day 1: the catalog (synthetic data). App tables (RFQs, quotes, AI logs) come in later migrations.

create extension if not exists vector;  -- pgvector, used for meaning-based search on Day 3

create table sellers (
  id            bigint primary key,
  name          text not null,
  city          text not null,
  country       text not null,
  shipping_fee  numeric(12, 2) not null check (shipping_fee >= 0)
);

create table parts (
  id                 bigint primary key,
  brand              text not null,
  part_number        text not null,
  part_number_norm   text not null,           -- '6205-2RS1' -> '62052RS1', for exact lookup
  category           text not null check (category in ('bearing', 'belt', 'filter', 'motor')),
  name               text not null,
  description        text not null,
  specs              jsonb not null,
  interchange_group  text not null,           -- same group = same physical part from another brand
  unique (brand, part_number)
);

create index parts_part_number_norm_idx on parts (part_number_norm);
create index parts_interchange_group_idx on parts (interchange_group);

-- What each seller carries: price, stock and lead time. Money is numeric, never float.
create table offers (
  seller_id       bigint not null references sellers (id),
  part_id         bigint not null references parts (id),
  unit_price      numeric(12, 2) not null check (unit_price > 0),
  currency        text not null default 'USD',
  stock_qty       integer not null check (stock_qty >= 0),
  lead_time_days  integer not null check (lead_time_days > 0),
  primary key (seller_id, part_id)
);

-- Row Level Security. Supabase exposes tables to the browser, so every table has RLS on.
-- Parts and sellers are a public catalog (read only). Offers (prices, stock) have no policy,
-- so only the backend can read them.
alter table sellers enable row level security;
alter table parts   enable row level security;
alter table offers  enable row level security;

create policy "catalog is public" on parts   for select using (true);
create policy "sellers are public" on sellers for select using (true);
