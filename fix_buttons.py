import glob, re

for f in glob.glob('pages/*.py') + ['app.py', 'playwright_engine.py']:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace width="stretch" with use_container_width=True for st.button and st.form_submit_button
    # Notice we don't replace it for st.data_editor or st.dataframe, which DO use width="stretch"!
    new_content = re.sub(r'(st\.button\([^)]*?)width=[\"\']stretch[\"\']', r'\1use_container_width=True', content)
    new_content = re.sub(r'(st\.form_submit_button\([^)]*?)width=[\"\']stretch[\"\']', r'\1use_container_width=True', new_content)
    
    if content != new_content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f'Fixed {f}')
