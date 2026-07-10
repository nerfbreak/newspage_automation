create table if not exists active_bot_tasks (
  id uuid primary key default gen_random_uuid(),
  task_type text not null,
  distributor_name text not null,
  started_by text not null,
  started_at timestamptz not null default now()
);
alter table active_bot_tasks enable row level security;
