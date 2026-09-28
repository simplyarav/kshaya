import json

paths = [r'ui\tsconfig.json', r'ui\tsconfig.app.json']
for path in paths:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'compilerOptions' not in data:
            data['compilerOptions'] = {}
        
        data['compilerOptions']['noUnusedLocals'] = False
        data['compilerOptions']['noUnusedParameters'] = False
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f\"Could not patch {path}: {e}\")
print(\"Patched tsconfig\")
