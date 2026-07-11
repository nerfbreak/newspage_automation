# Plan: Stock Mutation Auto-Approve & Screenshot for SA3 & SA4

## 1. Playwright Automation Additions
In `playwright_engine.py`, modify the success screenshot/reporting logic or general save sequence when executing `Stock Mutation` for `SA3` and `SA4`:
- If `REASON_CODE` is `SA3` or `SA4`:
  - After saving the document, instead of a plain screenshot or regular approved list check, we navigate to the list view (if not already there).
  - Select status `Open (Pending)` (Value: `O`) in status dropdown.
  - Click Search (`pag_I_StkAdj_grd_List_SearchForm_ButtonSearch_Value`).
  - Wait for the grid.
  - Locate and check the first row checkbox (`pag_I_StkAdj_grd_List_ctl02_chkDelete`).
  - Click Approve (`pag_I_StkAdj_btn_Approve_Value`).
  - Accept any confirmation alert dialog.
  - Wait for page/network to be ready.
  - Select status `Approved` (Value: `A`).
  - Click Search.
  - Sort by Stock Adjustment No descending (using `__doPostBack` twice just like the existing `_capture_stkadj_success_screenshot` script).
  - Double click the latest transaction link to open details.
  - Take detail screenshot.
  - Send to Telegram.

## 2. Integration Points
- Update `_capture_stkadj_success_screenshot` inside `playwright_engine.py` to support an optional parameter `approve_first` or custom workflow for `SA3`/`SA4`.
- Alternatively, check the `REASON_CODE` directly inside `_capture_stkadj_success_screenshot` (or pass it in).
- Make sure `is_mutasi` passes the chosen reason code down to `_capture_stkadj_success_screenshot` or uses it.
- In `run_execution_manual`, we call `_capture_stkadj_success_screenshot(page, TIMEOUT_MS, ui_log, "success_manual", reason_code=REASON_CODE)`.
