-- Property Sentence Labeler Database Schema
-- Tables: profiles, properties, sentences, labels

-- ==========================================
-- PROFILES TABLE (extends auth.users)
-- ==========================================
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  sentences_labeled integer default 0,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  last_login timestamp with time zone
);

alter table public.profiles enable row level security;

create policy "profiles_select_own" on public.profiles for select using (auth.uid() = id);
create policy "profiles_insert_own" on public.profiles for insert with check (auth.uid() = id);
create policy "profiles_update_own" on public.profiles for update using (auth.uid() = id);

-- ==========================================
-- PROPERTIES TABLE
-- ==========================================
create table if not exists public.properties (
  id uuid primary key default gen_random_uuid(),
  property_name text unique not null,
  property_domain text,
  property_range text,
  property_iri text,
  domain_iri text,
  range_iri text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.properties enable row level security;

-- Properties are readable by all authenticated users
create policy "properties_select_authenticated" on public.properties 
  for select to authenticated using (true);

-- ==========================================
-- SENTENCES TABLE
-- ==========================================
create table if not exists public.sentences (
  id uuid primary key default gen_random_uuid(),
  sentence text not null,
  property_id uuid not null references public.properties(id) on delete cascade,
  label_count integer default 0,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(sentence, property_id)
);

alter table public.sentences enable row level security;

-- Sentences are readable by all authenticated users
create policy "sentences_select_authenticated" on public.sentences 
  for select to authenticated using (true);

-- ==========================================
-- LABELS TABLE
-- ==========================================
create table if not exists public.labels (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  sentence_id uuid not null references public.sentences(id) on delete cascade,
  label_code text not null,
  subject_words text,
  object_words text,
  is_complete boolean default false,
  labeled_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(user_id, sentence_id)
);

alter table public.labels enable row level security;

-- Users can only see, insert, update, delete their own labels
create policy "labels_select_own" on public.labels for select using (auth.uid() = user_id);
create policy "labels_insert_own" on public.labels for insert with check (auth.uid() = user_id);
create policy "labels_update_own" on public.labels for update using (auth.uid() = user_id);
create policy "labels_delete_own" on public.labels for delete using (auth.uid() = user_id);

-- ==========================================
-- INDEXES for performance
-- ==========================================
create index if not exists idx_labels_user on public.labels(user_id);
create index if not exists idx_labels_sentence on public.labels(sentence_id);
create index if not exists idx_sentences_property on public.sentences(property_id);

-- ==========================================
-- TRIGGER: Auto-create profile on signup
-- ==========================================
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;

create trigger on_auth_user_created
  after insert on auth.users
  for each row
  execute function public.handle_new_user();
