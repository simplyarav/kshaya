import os
import glob

# Revert my cocoa brown mistakes to Teal Green from the prototype
replacements = {
    'bg-[#8B5A2B]': 'bg-[#7C9473]',
    'hover:bg-[#5C4033]': 'hover:bg-[#5F7562]',
    'text-[#8B5A2B]': 'text-[#7C9473]',
    'text-[#A0522D]': 'text-[#7C9473]', # previously blue-400
    'border-[#8B5A2B]': 'border-[#7C9473]',
    'focus:border-[#8B5A2B]': 'focus:border-[#7C9473]',
    'focus:ring-[#8B5A2B]': 'focus:ring-[#7C9473]',
    # Also I changed bg-[#2C425E] to bg-[#5C4033] in App.tsx for NavItem
    'bg-[#5C4033]': 'bg-[#7C9473]',
    'text-[#5C4033]': 'text-[#7C9473]'
}

files = glob.glob('ui/src/**/*.tsx', recursive=True)

for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('Colors reverted to Teal Green prototype style.')
