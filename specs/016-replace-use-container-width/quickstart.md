# Quickstart: Streamlit Layout Width Deprecation Migration

## Verification Procedure

To verify that the layout width parameters are successfully migrated and that no regressions are introduced:

1. **Verify Code Replacement**:
   Run a global search for `use_container_width` to ensure it is completely absent from the codebase:
   ```bash
   git grep "use_container_width"
   ```

2. **Run Streamlit Locally**:
   Start the local dev server:
   ```bash
   streamlit run app.py
   ```

3. **Manual Layout Validation**:
   - Access the dashboard and verify that all metric cards, buttons, and layouts render perfectly.
   - Navigate to each of the following pages:
     - **Inventory Adjustment**
     - **Sales Extraction**
     - **Promotion Comparison**
     - **Stock Mutation**
     - **Clearance Stock**
     - **Initial Stock**
   - Confirm that buttons stretch fully to their containers (where `True` was replaced with `'stretch'`) and do not drift visually.
