import os

path = r'ui\src\App.tsx'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(\"bg-[#2C425E] text-[#2E2B26]\", \"bg-[#5C4033] text-[#EDE6D6]\")
text = text.replace(\"bg-[#2C425E]\", \"bg-[#5C4033]\")

# Also change the icons in sidebar if any
text = text.replace(\"text-[#2C425E]\", \"text-[#5C4033]\")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print(\"Fixed App.tsx\")
