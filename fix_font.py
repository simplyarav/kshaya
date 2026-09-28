import os

path = r'ui\src\index.css'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace global Black Ops One with system-ui
text = text.replace(\"font-family: 'Black Ops One', system-ui, sans-serif !important;\", \"font-family: system-ui, sans-serif !important;\")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
