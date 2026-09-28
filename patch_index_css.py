import os

path = r'ui\src\index.css'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(\"@tailwind base;\\n@tailwind components;\\n@tailwind utilities;\", \"@import 'tailwindcss';\")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
