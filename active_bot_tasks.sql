-- SQL migration script to create active_bot_tasks table.
-- Run this in your Supabase SQL Editor.

create table if not exists active_bot_tasks (
  id uuid primary key default gen_random_uuid(),
  task_type text not null,
  distributor_name text not null,
  started_by text not null,
  started_at timestamptz not null default now()
);

-- Enable Row Level Security (RLS)
alter table active_bot_tasks enable row level security;

-- Add RLS policy allowing all authenticated users to read active tasks
create policy "Allow read for authenticated users" 
on active_bot_tasks 
for select 
to authenticated 
using (true);

-- Add RLS policy allowing authenticated users to insert/delete active tasks
create policy "Allow write for authenticated users" 
on active_bot_tasks 
for all 
to authenticated 
using (true)
with check (true);
