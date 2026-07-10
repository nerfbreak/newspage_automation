# Feature Implementation Plan: Bot Task Monitor Dashboard

## Context
The user requested a feature to display running bot tasks on the dashboard (`pages/0_dashboard.py`). This monitor should show:
- Which bot task is currently running.
- Which distributor is being processed.
- Which user is running the task.
- Display this information live/realtime on the dashboard so all users can see it, preventing duplicate work.
- Align with the Neo-Brutalism design system.

## Proposed Solution
1. **Database Tracking**: Create a new Supabase table or utilize an existing one to track "active_tasks". We will use the existing `extraction_history` and `adjustment_history` tables if they already track "running" status, or introduce a new `active_bot_tasks` table.
2. **Dashboard UI**: Add a Neo-Brutalism styled component to `pages/0_dashboard.py` that polls or fetches the active tasks from Supabase and displays them in a clear, visible format (e.g., a styled table or a list of active cards).
3. **Execution Engine Hooks**: Update `playwright_engine.py` (specifically `_wait_for_page_ready`, `run_execution_manual`, etc.) to register a task as "running" when it starts and clear it when it finishes (success, failure, or terminated). *Note: Modification of `playwright_engine.py` requires the unlock password. The user must provide it before implementation.*

## Supabase Schema Changes (if new table needed)
Table: `active_bot_tasks`
- `id` (uuid, pk)
- `task_type` (text) - e.g., "Stock Mutation", "Sales Extraction"
- `distributor_name` (text)
- `started_by` (text) - username
- `started_at` (timestamp)
- `status` (text) - "Running", "Stuck" (optional)

*Note: RLS policies must allow read for all authenticated users, and insert/delete for the user running the task.*

## UI Design (Neo-Brutalism)
- **Container**: `border: 3px solid #0F172A`, `box-shadow: 6px 6px 0px 0px #0F172A`, `background-color: #FFFFFF`, `border-radius: 0px`.
- **Badges**: Use primary color (`#0068C9`) or accent yellow (`#FFDE59`) for the "Running" status indicator.
- **Auto-Refresh**: Use `st_autorefresh` (if available and not conflicting with Streamlit cloud) or instruct users to refresh, or use a lightweight JS polling mechanism if real-time is strictly required without full page reload.

## Implementation Steps
1. **Request Password**: Ask the user for the "Dama" password to modify `playwright_engine.py` and `database.py`.
2. **Update Database Schema**: Execute SQL to create the tracking table (if applicable) and write `database.py` functions to register/unregister tasks.
3. **Update Dashboard UI**: Add the "Active Bot Tasks" section to `pages/0_dashboard.py`.
4. **Update Playwright Hooks**: Inject registration and deregistration calls in `playwright_engine.py` execution flows.
