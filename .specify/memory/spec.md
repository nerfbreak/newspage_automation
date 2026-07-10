# Spec: Bot Task Monitor Dashboard

## Objective
Display active bot tasks in real-time on the dashboard (task type, distributor, user) to prevent duplicate work.

## Assumptions
- Uses Supabase `active_bot_tasks` table.
- Dashboard will fetch and render list of tasks using Neo-Brutalism styling.
- `playwright_engine.py` functions will register on start and clear on exit/terminate. (Unlocked via Dama).

## Requirements
- Add `active_bot_tasks` table checking to schema check.
- Add `register_active_task`, `clear_active_task`, `get_active_tasks` to `database.py`.
- Render tasks as cards with 3px `#0F172A` borders, `#FFFFFF` bg, and `#0068C9` or `#FFDE59` accents in `pages/0_dashboard.py`.
- `playwright_engine.py` must register/clear tasks around `run_execution`, `run_execution_manual`, `run_extract`, `run_sales_extract`, `run_promotion_sync`, `run_mutasi_execution`.

## Acceptance Criteria
- [ ] Active bot runs appear on the dashboard.
- [ ] Active tasks disappear when complete/terminated.
- [ ] UI matches Neo-Brutalism tokens.
