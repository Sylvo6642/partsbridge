-- Day 3: two ways to search the catalog besides exact part numbers.

-- 1. Keyword search (Postgres full-text search).
--    'english' reduces words to their stem, so "bearings" matches "bearing" and "sealed" matches "seal".
alter table parts add column search_tsv tsvector
  generated always as (to_tsvector('english', name || ' ' || description)) stored;
create index parts_search_tsv_idx on parts using gin (search_tsv);

-- 2. Meaning search (pgvector). Each part's text is turned into 1536 numbers by text-embedding-3-small;
--    parts with similar meaning have nearby vectors. Filled by scripts/embed_catalog.py.
alter table parts add column embedding vector(1536);
create index parts_embedding_idx on parts using hnsw (embedding vector_cosine_ops);
