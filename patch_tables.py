import re

with open('static/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

# 1. Fix dataframes
dataframe_css = """
/* --- Neo-Brutalist DataFrames --- */
div[data-testid="stDataFrame"] {
    border: 3px solid #0F172A !important;
    border-radius: 0px !important;
    box-shadow: 6px 6px 0px 0px #0F172A !important;
    background-color: #FFFFFF !important;
    margin-bottom: 24px !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
div[data-testid="stDataFrame"]:hover {
    transform: translate(-2px, -2px) !important;
    box-shadow: 8px 8px 0px 0px #0F172A !important;
}
"""
if 'Neo-Brutalist DataFrames' not in css:
    css = css.replace('/* --- Native st.dataframe Scrollbar Hide --- */', dataframe_css + '\n/* --- Native st.dataframe Scrollbar Hide --- */')

# 2. Fix metric boxes
css = re.sub(r'\.metric-box-match, \.metric-box-mismatch \{.*?\n\}', 
    '.metric-box-match, .metric-box-mismatch {\\n    background-color: #FFFFFF;\\n    border: 3px solid #0F172A !important;\\n    border-radius: 0px !important;\\n    padding: 16px 20px;\\n    margin-bottom: 16px;\\n    box-shadow: 6px 6px 0px 0px #0F172A !important;\\n    transition: transform 0.15s ease, box-shadow 0.15s ease !important;\\n}\\n.metric-box-match:hover, .metric-box-mismatch:hover {\\n    transform: translate(-2px, -2px) !important;\\n    box-shadow: 8px 8px 0px 0px #0F172A !important;\\n}', 
    css, flags=re.DOTALL)
css = re.sub(r'\.metric-box-match\s*\{\s*border-left: 4px solid #0068C9;\s*\}', '', css)
css = re.sub(r'\.metric-box-mismatch\s*\{\s*border-left: 4px solid #FF2B2B;\s*\}', '', css)

# 3. Fix notifications (remove left border)
css = re.sub(r'border-left: 8px solid #[0-9a-fA-F]+ !important;', 'border: 3px solid #0F172A !important; border-radius: 0px !important;', css)
css = css.replace('border-left: 4px solid #0068C9', 'border: 3px solid #0F172A !important; border-radius: 0px !important;')

# 4. In utils.py, remove border-left from alert boxes
with open('utils.py', 'r', encoding='utf-8') as f:
    utils_py = f.read()
utils_py = re.sub(r'border-left:\s*\{border_left\};', 'border: 3px solid #0F172A; border-radius: 0px;', utils_py)

with open('static/style.css', 'w', encoding='utf-8') as f:
    f.write(css)
with open('utils.py', 'w', encoding='utf-8') as f:
    f.write(utils_py)

print('Patched dataframes, metric boxes, and alert boxes!')
