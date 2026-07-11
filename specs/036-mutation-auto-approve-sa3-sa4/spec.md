# Spec: Stock Mutation Auto-Approve & Screenshot for SA3 & SA4

## 1. Overview
When performing Stock Mutation in Newspage, if the chosen Reason Adjustment is `SA3 - Transfer Gudang Internal` or `SA4 - Transfer Gudang Eksternal`, the system must automatically execute an Approval workflow on the Newspage portal right after the adjustment document is saved.

## 2. Requirements & Workflow
After saving the adjustment row / document for SA3 or SA4:
1. Filter the list view by Status `Open (Pending)`.
2. Click the `Search` button:
   - ID: `pag_I_StkAdj_grd_List_SearchForm_ButtonSearch_Value`
3. Click the checkbox on the first/latest row:
   - ID: `pag_I_StkAdj_grd_List_ctl02_chkDelete`
4. Click the `Approve` button:
   - ID: `pag_I_StkAdj_btn_Approve_Value`
5. Filter status back to `Approved`.
6. Click the `Search` button again.
7. Double-click the latest Stock Adjustment No (similar to the logic in Inventory Adjustment) to open the record details.
8. Take a screenshot of the opened record.
9. Send the screenshot to Telegram.

## 3. Scope & Boundaries
- Only triggers when `REASON_CODE` is `SA3` or `SA4`.
- Extends the existing `_capture_stkadj_success_screenshot` or a dedicated helper inside `playwright_engine.py` to handle the approval flow.
- Integrates with the Stock Mutation execution flow in `playwright_engine.py`.
