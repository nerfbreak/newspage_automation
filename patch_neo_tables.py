import re
import glob

# 1. Add CSS for neo-table to style.css
with open('static/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

if '.neo-table-wrapper' not in css:
    table_css = '''
/* --- True Neo-Brutalist HTML Tables (st.markdown fallback) --- */
.neo-table-wrapper {
    max-height: 400px;
    overflow-y: auto;
    border: 3px solid #0F172A;
    box-shadow: 6px 6px 0px 0px #0F172A;
    background-color: #FFFFFF;
    margin-bottom: 24px;
}
table.neo-table {
    width: 100%;
    border-collapse: collapse;
}
table.neo-table th, table.neo-table td {
    border: 2px solid #0F172A;
    padding: 10px 14px;
    color: #0F172A;
    font-size: 0.85rem;
    font-family: "Source Sans 3", sans-serif;
}
table.neo-table th {
    background-color: #f1f5f9;
    font-weight: 800;
    text-transform: uppercase;
    position: sticky;
    top: 0;
    z-index: 1;
}
'''
    css += table_css
    with open('static/style.css', 'w', encoding='utf-8') as f:
        f.write(css)

# 2. Patch pages to use utils.render_neo_table
# We need to make sure utils is imported! 
# In pages, they usually import utils.
for file in glob.glob('pages/*.py'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'st.dataframe(' in content or '.dataframe(' in content:
        # We need to replace st.dataframe(df, ...) with utils.render_neo_table(df)
        # And table_placeholder.dataframe(df, ...) with utils.render_neo_table(table_placeholder, df)
        
        # 1_inventory_adjustment.py replacements
        content = re.sub(r'st\.dataframe\(st\.session_state\.reconcile_summary\[\'df_view\'\].*?\)', 
                         r'utils.render_neo_table(st.session_state.reconcile_summary[\'df_view\'])', content)
                         
        content = re.sub(r'table_placeholder\.dataframe\(df_view.*?\)', 
                         r'utils.render_neo_table(table_placeholder, df_view)', content)
                         
        content = re.sub(r'table_placeholder\.dataframe\(df_exec.*?\)', 
                         r'utils.render_neo_table(table_placeholder, df_exec)', content)
                         
        # General st.dataframe fallback if we missed any specific ones
        # Actually, it's safer to only replace what we know. Let's do a simple regex for st.dataframe(X, hide_index...)
        content = re.sub(r'st\.dataframe\(([^,]+)(, [^)]+)?\)', r'utils.render_neo_table(\1)', content)
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)

print('Patched dataframes to use neo_table!')
