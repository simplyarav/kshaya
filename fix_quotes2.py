import glob
import os

files = [
    'scripts/validate_device_detection.py',
    'scripts/prepare_real_test_image.py',
    'scripts/platform_capability_check.py',
    'tests/test_real_hardware_sanitization.py',
    'tests/test_real_recovery_pipeline.py'
]

for filepath in files:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='mbcs') as f:
            content = f.read()
        
        content = content.replace('\\"', '"')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {filepath}")
