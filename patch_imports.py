import glob
import os

for file in glob.glob('pages/*.py'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'utils.' in content and 'import utils' not in content:
        # Inject 'import utils' after 'import streamlit as st'
        if 'import streamlit as st' in content:
            content = content.replace('import streamlit as st', 'import streamlit as st\nimport utils')
        else:
            content = 'import utils\n' + content
            
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Injected import utils to {file}')
