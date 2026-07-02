import re

def remove_hover_expansion(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace 8px 8px shadow with 6px 6px shadow (which matches normal state, effectively removing the size change)
    content = re.sub(r'box-shadow:\s*8px\s+8px\s+0px\s+0px\s+#[0-9a-fA-F]+(\s*!important)?;?', '', content)
    # Actually, if I completely remove the box-shadow property from the hover block, it will inherit the 6px 6px from the normal state!
    # So deleting it is better than setting it to 6px 6px (less redundant CSS).
    
    # Let's remove the transform: translate(-2px, -2px) entirely
    content = re.sub(r'transform:\s*translate\(\s*-2px\s*,\s*-2px\s*\)(\s*!important)?\s*;?', '', content)
    
    # Also clean up empty hover blocks if any, though CSS doesn't break if there are empty blocks.
    
    # Let's write it back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

remove_hover_expansion('static/style.css')
remove_hover_expansion('utils.py')
print('Removed hover expansion!')
