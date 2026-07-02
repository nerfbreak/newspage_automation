import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """            changelog_content = "".join(lines[start_idx:])
            st.markdown(changelog_content)"""

new_block = """            changelog_content = "".join(lines[start_idx:])
            
            # Neo-Brutalist Changelog Headers
            changelog_content = changelog_content.replace(
                "### ✨ Fitur Baru", 
                "<h3><span style='background: #A3E635; border: 3px solid #0F172A; box-shadow: 4px 4px 0px 0px #0F172A; padding: 4px 12px; font-weight: 900; font-family: \"Courier New\", Courier, monospace; letter-spacing: 0.05em; text-transform: uppercase;'>★ NEW FEATURES</span></h3><br>"
            )
            changelog_content = changelog_content.replace(
                "### 🛠️ Perbaikan & Peningkatan", 
                "<h3><span style='background: #FBBF24; border: 3px solid #0F172A; box-shadow: 4px 4px 0px 0px #0F172A; padding: 4px 12px; font-weight: 900; font-family: \"Courier New\", Courier, monospace; letter-spacing: 0.05em; text-transform: uppercase;'>⚡ IMPROVEMENTS</span></h3><br>"
            )
            st.markdown(changelog_content, unsafe_allow_html=True)"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched app.py")
else:
    print("Could not find block in app.py")
