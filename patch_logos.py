import os

files = [r'ui\src\App.tsx', r'ui\src\components\FirstRunSetup.tsx', r'ui\src\components\Login.tsx']

for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # We replaced text-blue-500 -> text-[#8B5A2B] and text-[#5C4033] (I manually replaced it in App.tsx)
    text = text.replace(\"text-[#5C4033]\", \"text-[#7C9473]\")
    text = text.replace(\"text-[#8B5A2B]\", \"text-[#7C9473]\")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
print(\"Patched teal green\")
