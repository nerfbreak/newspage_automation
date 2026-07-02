import os
import re

# 1. Restore style.css to its original committed state
os.system('git checkout HEAD -- static/style.css')

with open('static/style.css', 'r') as f:
    css = f.read()

# 2. Re-apply the fixes on the pristine file
# Fix DASHBOARD button
css = css.replace('border-radius: 4px !important;', 'border-radius: 0px !important;')

# Fix remaining blue shadows to #0F172A
css = re.sub(r'(box-shadow:[^;]+)#0068C9', r'\1#0F172A', css, flags=re.IGNORECASE)
css = re.sub(r'(border-color:[^;]+)#0068C9', r'\1#0F172A', css, flags=re.IGNORECASE)

# Remove the old Scrollable Container Border Fix block to prevent conflicts
css = re.sub(r'/\* Scrollable Container Border Fix \*/.*?div\[data-testid="stVerticalBlockBorderWrapper"\] \{.*?\}', '', css, flags=re.DOTALL)

# Update the end of the file container css to be bulletproof
css = re.sub(r'div\[data-testid="stVerticalBlockBorderWrapper"\] \{.*?\}', '', css, flags=re.DOTALL)
css = re.sub(r'div\[data-testid="stVerticalBlockBorderWrapper"\]:hover \{.*?\}', '', css, flags=re.DOTALL)
css = re.sub(r'div\[data-testid="stVerticalBlockBorderWrapper"\] > div \{.*?\}', '', css, flags=re.DOTALL)

broad_container_css = '''
/* --- BULLETPROOF NEO-BRUTALIST CONTAINERS --- */
div[data-testid="stVerticalBlockBorderWrapper"],
/* Fallbacks for Streamlit 1.35 containers */
div.st-emotion-cache-1jicfl2,
div[data-testid="stVerticalBlock"] > div.st-emotion-cache-1wmy9hl {
    border-radius: 0px !important;
    border: 3px solid #0F172A !important;
    box-shadow: 6px 6px 0px 0px #0F172A !important;
    background-color: #FFFFFF !important;
    overflow: visible !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover,
div.st-emotion-cache-1jicfl2:hover {
    transform: translate(-2px, -2px) !important;
    box-shadow: 8px 8px 0px 0px #0F172A !important;
}

/* Strip inner borders to avoid double borders */
div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
}
'''

css += broad_container_css

with open('static/style.css', 'w') as f:
    f.write(css)

print('Clean and patched successfully!')
