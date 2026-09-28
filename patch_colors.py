import os
import glob

replacements = {
    'bg-blue-600': 'bg-[#8B5A2B]',
    'hover:bg-blue-500': 'hover:bg-[#5C4033]',
    'text-blue-600': 'text-[#8B5A2B]',
    'text-blue-500': 'text-[#8B5A2B]',
    'text-blue-400': 'text-[#A0522D]',
    'text-blue-300': 'text-[#DCD4C0]',
    'border-blue-500': 'border-[#8B5A2B]',
    'bg-blue-900': 'bg-[#8B5A2B]',
    'focus:border-blue-500': 'focus:border-[#8B5A2B]',
    'focus:ring-blue-500': 'focus:ring-[#8B5A2B]',
    'text-white': 'text-[#2E2B26]', 
    'text-gray-100': 'text-[#4A3B32]',
    'text-gray-200': 'text-[#4A3B32]',
    'text-gray-300': 'text-[#5C4033]',
    'text-gray-400': 'text-[#5C4033]',
    'bg-gray-950': 'bg-[#EDE6D6]',
    'bg-gray-900': 'bg-[#F5F1E7]',
    'bg-gray-800': 'bg-[#DCD4C0]',
    'border-gray-800': 'border-[#C7BFA6]',
    'border-gray-700': 'border-[#C7BFA6]',
    'border-gray-600': 'border-[#C7BFA6]'
}

files = glob.glob('ui/src/**/*.tsx', recursive=True)

for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We want to replace carefully, but string replace is fine for tailwind classes
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print(f'Replaced in {len(files)} files.')
