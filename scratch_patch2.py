import glob
import re

for file in glob.glob('pages/*.py'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We want to match: (spaces)with st.container(...):
    # But only if it has border=True or height=
    # Avoid double injecting
    if 'neo-container-marker' in content:
        # Strip existing markers to prevent duplicates
        content = re.sub(r'^[ \t]*st\.markdown\("<span class=\'neo-container-marker\'></span>", unsafe_allow_html=True\)\n', '', content, flags=re.MULTILINE)

    def replacer(match):
        spaces = match.group(1)
        original = match.group(0)
        return f'{spaces}st.markdown("<span class=\'neo-container-marker\'></span>", unsafe_allow_html=True)\n{original}'
        
    new_content = re.sub(r'^([ \t]*)with st\.container\((.*?border=True.*?|.*?height=.*?)\):', replacer, content, flags=re.MULTILINE)
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(new_content)
print('Patched all pages!')
