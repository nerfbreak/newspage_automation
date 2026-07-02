import re

with open('utils.py', 'r', encoding='utf-8') as f:
    utils_code = f.read()

# Inject render_neo_table function
if 'def render_neo_table' not in utils_code:
    neo_table_func = '''
def render_neo_table(df_or_placeholder, df=None):
    """
    Renders a neo-brutalist table.
    Can be called as render_neo_table(df) or render_neo_table(placeholder, df)
    """
    import pandas as pd
    if df is None:
        target_df = df_or_placeholder
        target = st
    else:
        target_df = df
        target = df_or_placeholder
        
    if not isinstance(target_df, pd.DataFrame):
        target_df = pd.DataFrame(target_df)
        
    html = target_df.to_html(index=False, classes="neo-table", escape=True)
    html_str = f'<div class="neo-table-wrapper">{html}</div>'
    target.markdown(html_str, unsafe_allow_html=True)
'''
    utils_code += neo_table_func

with open('utils.py', 'w', encoding='utf-8') as f:
    f.write(utils_code)

print("Injected render_neo_table to utils.py")
