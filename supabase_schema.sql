-- Run once in a dedicated personal Supabase project's SQL Editor.
create table if not exists public.pocketfolio_documents (
  id text primary key,
  kind text not null check (kind in ('journal', 'portfolio')),
  payload jsonb not null,
  revision integer not null default 1 check (revision > 0),
  updated_at timestamptz not null default now(),
  deleted boolean not null default false
);
create index if not exists pocketfolio_kind_updated
  on public.pocketfolio_documents (kind, updated_at desc);
alter table public.pocketfolio_documents enable row level security;
revoke all on public.pocketfolio_documents from anon, authenticated;
grant select, insert, update, delete on public.pocketfolio_documents to service_role;
-- No public policies. Only the server-held secret/service_role key can access.
-- App owner authentication in access.py is required before constructing this store.
