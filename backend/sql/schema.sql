-- mart-pick schema
-- Run this in the Supabase project's SQL editor once the project exists.

create table if not exists markets (
  id bigint generated always as identity primary key,
  name text not null,
  -- scraper-specific key so an ingestion job can find "which market is this
  -- flyer for" again (e.g. smk.kr's shopid like 's7775'). null for markets
  -- entered by hand with no automated source yet.
  source_type text,        -- e.g. 'smk_kakao_flyer'
  source_key text,         -- e.g. shopid 's7775'
  phone text,
  address text,
  created_at timestamptz not null default now(),
  unique (source_type, source_key)
);

-- Raw, ungrouped price observations. One row per (market, day, item) seen in
-- a scraped flyer. Deliberately NOT deduplicated against a canonical
-- "products" table yet - the same real-world item shows up under different
-- names at different marts (e.g. "우유 1L" vs "서울우유 1L"), and matching
-- those across marts is a separate, harder step to tackle once there's
-- enough real data to see how much the naming actually varies.
create table if not exists price_snapshots (
  id bigint generated always as identity primary key,
  market_id bigint not null references markets(id) on delete cascade,
  scraped_at date not null default current_date,
  category text,
  item_name text not null,
  item_option text,
  price integer not null,
  original_price integer,
  -- discount wording, limited-day labels etc that didn't fit price/option
  -- (e.g. "즉시할인 2,000원 적용가"). Only set by the OCR pipeline for now.
  note text,
  created_at timestamptz not null default now(),
  unique (market_id, scraped_at, item_name, item_option)
);

create index if not exists price_snapshots_item_name_idx
  on price_snapshots (item_name);
create index if not exists price_snapshots_market_date_idx
  on price_snapshots (market_id, scraped_at);
