import re

def process_css_content(content):
    # Split into blocks
    blocks = re.split(r'(?<=})', content)
    new_blocks = []
    
    for block in blocks:
        if not block.strip():
            new_blocks.append(block)
            continue
            
        # Is this a hover block?
        is_hover = ':hover' in block
        is_active = ':active' in block
        
        # We want everything uniform.
        # Normal state shadow: 6px 6px 0px 0px #0F172A
        # Hover state shadow: 8px 8px 0px 0px #0F172A
        # Active state shadow: 2px 2px 0px 0px #0F172A
        
        # Find if there is a box-shadow rule
        if 'box-shadow:' in block and 'none' not in block and 'transparent' not in block:
            if is_active:
                block = re.sub(r'box-shadow:\s*\d+px\s+\d+px\s+0px\s+0px\s+#[0-9a-fA-F]+(\s*!important)?', r'box-shadow: 2px 2px 0px 0px #0F172A\1', block)
            elif is_hover:
                block = re.sub(r'box-shadow:\s*\d+px\s+\d+px\s+0px\s+0px\s+#[0-9a-fA-F]+(\s*!important)?', r'box-shadow: 8px 8px 0px 0px #0F172A\1', block)
            else:
                block = re.sub(r'box-shadow:\s*\d+px\s+\d+px\s+0px\s+0px\s+#[0-9a-fA-F]+(\s*!important)?', r'box-shadow: 6px 6px 0px 0px #0F172A\1', block)
        
        new_blocks.append(block)
        
    return "".join(new_blocks)

def normalize_shadows(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = process_css_content(content)
    
    # Also handle inline styles in utils.py (they don't have :hover in the same way, but let's check)
    if filepath == 'utils.py':
        # Just replace any 4px with 6px for normal inline styles
        new_content = re.sub(r'box-shadow:\s*4px\s+4px\s+0px\s+0px\s+#[0-9a-fA-F]+', 'box-shadow: 6px 6px 0px 0px #0F172A', new_content)
        new_content = re.sub(r'shadow\s*=\s*"4px\s+4px\s+0px\s+0px\s+#[0-9a-fA-F]+"', 'shadow = "6px 6px 0px 0px #0F172A"', new_content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

normalize_shadows('static/style.css')
normalize_shadows('utils.py')
print('Normalized shadows with intelligent hover states!')
