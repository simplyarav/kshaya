import os
import glob
import re

files = glob.glob('ui/src/components/*.tsx')

for path in files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove max-w-* mx-auto from main wrapper divs
    content = re.sub(r'max-w-[a-zA-Z0-9]+ mx-auto', '', content)
    
    # Fix any double spaces or leading spaces left behind in classNames
    content = content.replace('className=\" ', 'className=\"')
    content = content.replace('className=\"  ', 'className=\"')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('Removed mx-auto constraints')
